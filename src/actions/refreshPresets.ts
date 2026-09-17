import streamDeck, { action, type KeyDownEvent, type SendToPluginEvent, SingletonAction } from "@elgato/streamdeck";
import type { JsonValue } from "@elgato/utils";

import { errorMessage, type LightroomConnection } from "../lightroom/connection.js";
import type { PresetManager } from "../lightroom/presetManager.js";
import type { ApplyPresetAction } from "./applyPreset.js";

/**
 * "Refresh Lightroom Presets" - a standalone command action that
 * re-discovers presets from Lightroom, updates the shared cache, and flags
 * any "Apply Lightroom Preset" buttons whose assigned preset disappeared.
 */
@action({ UUID: "com.keelan182.lightroom-presets.refresh-presets" })
export class RefreshPresetsAction extends SingletonAction<Record<string, never>> {
	constructor(
		private readonly connection: LightroomConnection,
		private readonly presetManager: PresetManager,
		private readonly applyPresetAction: ApplyPresetAction,
	) {
		super();
	}

	public override async onKeyDown(ev: KeyDownEvent<Record<string, never>>): Promise<void> {
		if (!ev.action.isKey()) {
			return;
		}

		if (this.connection.getStatus() !== "connected") {
			streamDeck.logger.warn(`Refresh requested but Lightroom is not connected (status: ${this.connection.getStatus()})`);
			await ev.action.showAlert();
			await this.flash(ev.action, "No\nConnection");
			return;
		}

		try {
			const { presets, removedIds } = await this.presetManager.refresh();
			await this.applyPresetAction.reconcileAssignments(removedIds);
			await ev.action.showOk();
			await this.flash(ev.action, `${presets.length}\nPresets`);
			streamDeck.logger.info(`Refreshed ${presets.length} presets (${removedIds.length} removed)`);
		} catch (err) {
			streamDeck.logger.error(`Preset refresh failed: ${errorMessage(err)}`);
			await ev.action.showAlert();
			await this.flash(ev.action, "Refresh\nFailed");
		}
	}

	public override async onSendToPlugin(ev: SendToPluginEvent<JsonValue, Record<string, never>>): Promise<void> {
		const payload = ev.payload;
		if (payload !== null && typeof payload === "object" && !Array.isArray(payload) && (payload as Record<string, unknown>).event === "refreshPresets") {
			try {
				const { removedIds } = await this.presetManager.refresh();
				await this.applyPresetAction.reconcileAssignments(removedIds);
			} catch (err) {
				streamDeck.logger.error(`Refresh from property inspector failed: ${errorMessage(err)}`);
			}
		}
	}

	private async flash(action: KeyDownEvent<Record<string, never>>["action"], text: string): Promise<void> {
		if (!action.isKey()) {
			return;
		}
		await action.setTitle(text);
		setTimeout(() => {
			action.setTitle(undefined).catch(() => undefined);
		}, 1800);
	}
}
