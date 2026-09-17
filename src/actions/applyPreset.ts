import streamDeck, {
	action,
	type DidReceiveSettingsEvent,
	type KeyAction,
	type KeyDownEvent,
	type SendToPluginEvent,
	SingletonAction,
	type WillAppearEvent,
} from "@elgato/streamdeck";
import type { JsonValue } from "@elgato/utils";

import { errorMessage, type LightroomConnection } from "../lightroom/connection.js";
import type { PresetApplicationService } from "../lightroom/presetApplication.js";
import type { PresetManager } from "../lightroom/presetManager.js";
import type { ApplyPresetSettings, LightroomConnectionStatus, PluginGlobalSettings } from "../lightroom/types.js";
import { PresetApplicationError } from "../lightroom/types.js";

const FEEDBACK_DURATION_MS = 1300;
const ERROR_FEEDBACK_DURATION_MS = 2600;

type DataSourceItem = { value: string; label: string };
type DataSourceGroup = { label: string; children: DataSourceItem[] };
type DataSourceEntry = DataSourceItem | DataSourceGroup;

type PropertyInspectorEvent = "getPresets" | "refreshPresets" | "toggleFavorite";

function isPropertyInspectorMessage(payload: JsonValue): payload is { event: PropertyInspectorEvent; presetId?: string } {
	return (
		payload !== null &&
		typeof payload === "object" &&
		!Array.isArray(payload) &&
		typeof (payload as Record<string, unknown>).event === "string"
	);
}

/**
 * "Apply Lightroom Preset" - the primary action. Each button instance stores
 * its own preset id/name and title preference in its action settings, so
 * multiple buttons never share state (Stream Deck settings are already
 * per-instance; we simply never read/write global state for the assignment
 * itself, only for favorites).
 */
@action({ UUID: "com.keelan182.lightroom-presets.apply-preset" })
export class ApplyPresetAction extends SingletonAction<ApplyPresetSettings> {
	constructor(
		private readonly connection: LightroomConnection,
		private readonly presetManager: PresetManager,
		private readonly presetApplication: PresetApplicationService,
	) {
		super();
	}

	public override async onWillAppear(ev: WillAppearEvent<ApplyPresetSettings>): Promise<void> {
		if (!ev.action.isKey()) {
			return;
		}
		await this.applyTitle(ev.action, ev.payload.settings);
	}

	public override async onDidReceiveSettings(ev: DidReceiveSettingsEvent<ApplyPresetSettings>): Promise<void> {
		if (!ev.action.isKey()) {
			return;
		}
		await this.applyTitle(ev.action, ev.payload.settings);
	}

	public override async onKeyDown(ev: KeyDownEvent<ApplyPresetSettings>): Promise<void> {
		if (!ev.action.isKey()) {
			return;
		}
		const settings = ev.payload.settings;

		try {
			await this.presetApplication.apply(settings.presetId);
			await ev.action.showOk();
			await this.flashTitle(ev.action, "✓", settings, FEEDBACK_DURATION_MS);
		} catch (err) {
			await ev.action.showAlert();
			const message = err instanceof Error ? err.message : errorMessage(err);
			streamDeck.logger.error(`Apply preset failed: ${message}`);
			await this.flashTitle(ev.action, shortErrorLabel(err), settings, ERROR_FEEDBACK_DURATION_MS);
		}
	}

	public override async onSendToPlugin(ev: SendToPluginEvent<JsonValue, ApplyPresetSettings>): Promise<void> {
		const payload = ev.payload;
		if (!isPropertyInspectorMessage(payload)) {
			return;
		}

		switch (payload.event) {
			case "getPresets":
				await this.sendPresetDataSource();
				return;
			case "refreshPresets":
				await this.handleRefreshFromPropertyInspector();
				return;
			case "toggleFavorite":
				if (payload.presetId) {
					await this.toggleFavorite(payload.presetId);
				}
				await this.sendPresetDataSource();
				return;
		}
	}

	/** Called by the "Refresh Lightroom Presets" action after it re-discovers presets. */
	public async reconcileAssignments(removedIds: string[]): Promise<void> {
		if (removedIds.length === 0) {
			return;
		}
		const removed = new Set(removedIds);

		for (const visible of this.actions) {
			if (!visible.isKey()) {
				continue;
			}
			const settings = await visible.getSettings<ApplyPresetSettings>();
			if (settings.presetId && removed.has(settings.presetId)) {
				streamDeck.logger.warn(`Button assignment no longer exists in Lightroom: ${settings.presetName ?? settings.presetId}`);
				await visible.showAlert();
				await visible.setTitle(`Preset not found:\n${settings.presetName ?? settings.presetId}`);
			}
		}
	}

	/** Re-renders titles that include the live connection status; called on every status change. */
	public async refreshTitlesForStatus(status: LightroomConnectionStatus): Promise<void> {
		for (const visible of this.actions) {
			if (!visible.isKey()) {
				continue;
			}
			const settings = await visible.getSettings<ApplyPresetSettings>();
			if (settings.titleMode === "preset-and-status") {
				await visible.setTitle(this.computeTitle(settings, status));
			}
		}
	}

	private async handleRefreshFromPropertyInspector(): Promise<void> {
		try {
			const { removedIds } = await this.presetManager.refresh();
			await this.reconcileAssignments(removedIds);
			await this.sendPresetDataSource();
		} catch (err) {
			streamDeck.logger.error(`Refresh from property inspector failed: ${errorMessage(err)}`);
		}
	}

	private async toggleFavorite(presetId: string): Promise<void> {
		const globalSettings = await streamDeck.settings.getGlobalSettings<PluginGlobalSettings>();
		const favorites = new Set(globalSettings.favoritePresetIds ?? []);
		if (favorites.has(presetId)) {
			favorites.delete(presetId);
		} else {
			favorites.add(presetId);
		}
		await streamDeck.settings.setGlobalSettings<PluginGlobalSettings>({
			...globalSettings,
			favoritePresetIds: [...favorites],
		});
	}

	private async sendPresetDataSource(): Promise<void> {
		const globalSettings = await streamDeck.settings.getGlobalSettings<PluginGlobalSettings>();
		const favorites = new Set(globalSettings.favoritePresetIds ?? []);
		const presets = this.presetManager.getPresets();

		const items: DataSourceEntry[] = [];

		if (presets.length === 0) {
			await streamDeck.ui.sendToPropertyInspector({
				event: "getPresets",
				items: [{ value: "", label: "No presets cached yet - click Refresh Presets" }],
			});
			return;
		}

		const favoritePresets = presets.filter((preset) => favorites.has(preset.id));
		if (favoritePresets.length > 0) {
			items.push({
				label: "★ Favorites",
				children: favoritePresets.map((preset) => ({ value: preset.id, label: preset.name })),
			});
		}

		items.push({
			label: "All Presets",
			children: presets.map((preset) => ({
				value: preset.id,
				label: favorites.has(preset.id) ? `★ ${preset.name}` : preset.name,
			})),
		});

		await streamDeck.ui.sendToPropertyInspector({ event: "getPresets", items });
	}

	private async flashTitle(action: KeyAction<ApplyPresetSettings>, text: string, settings: ApplyPresetSettings, durationMs: number): Promise<void> {
		await action.setTitle(text);
		setTimeout(() => {
			this.applyTitle(action, settings).catch((err) => streamDeck.logger.error(`Failed to restore title: ${errorMessage(err)}`));
		}, durationMs);
	}

	private async applyTitle(action: KeyAction<ApplyPresetSettings>, settings: ApplyPresetSettings): Promise<void> {
		const title = this.computeTitle(settings, this.connection.getStatus());
		await action.setTitle(title);

		// Backfill presetName so we can still show a meaningful label if this
		// preset later disappears from the cache (renamed/deleted in Lightroom).
		const resolved = settings.presetId ? this.presetManager.findById(settings.presetId) : undefined;
		if (resolved && resolved.name !== settings.presetName) {
			await action.setSettings({ ...settings, presetName: resolved.name });
		}
	}

	private computeTitle(settings: ApplyPresetSettings, status: LightroomConnectionStatus): string {
		if (settings.titleMode === "custom") {
			return settings.customTitle && settings.customTitle.length > 0 ? settings.customTitle : "Apply Preset";
		}

		const name = (settings.presetId && this.presetManager.findById(settings.presetId)?.name) ?? settings.presetName;

		if (!name) {
			return "Select\nPreset";
		}

		if (settings.titleMode === "preset-and-status") {
			return `${name}\n${statusGlyph(status)}`;
		}

		return name;
	}
}

function statusGlyph(status: LightroomConnectionStatus): string {
	switch (status) {
		case "connected":
			return "●";
		case "connecting":
			return "◐";
		case "not-running":
			return "○ No LR";
		case "unresponsive":
			return "○ Wait";
		case "disconnected":
		default:
			return "○ Off";
	}
}

function shortErrorLabel(err: unknown): string {
	if (err instanceof PresetApplicationError) {
		switch (err.code) {
			case "not-running":
				return "No\nLightroom";
			case "disconnected":
				return "Not\nConnected";
			case "unresponsive":
				return "No\nResponse";
			case "preset-not-found":
				return "Preset\nNot Found";
			case "no-preset-configured":
				return "Set a\nPreset";
			default:
				return "LR\nError";
		}
	}
	return "LR\nError";
}
