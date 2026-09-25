import streamDeck, { action, type KeyDownEvent, SingletonAction, type WillAppearEvent } from "@elgato/streamdeck";

import { errorMessage, type LightroomConnection } from "../lightroom/connection.js";
import { DEVELOP_TOGGLES, type DevelopControlService } from "../lightroom/developControl.js";
import { PresetApplicationError } from "../lightroom/types.js";

type ToggleLensCorrectionSettings = {
	settingId?: string;
	/**
	 * Locally-tracked last known state. Lightroom's External Controller API
	 * has no way to read a setting's current value back (see
	 * docs/PROTOCOL.md), so this can drift out of sync if the same setting
	 * is changed directly inside Lightroom - the button always shows what
	 * this plugin last set, not necessarily Lightroom's true current state.
	 */
	isOn?: boolean;
};

/**
 * "Toggle Lens Correction" - flips an on/off Develop setting (lens profile
 * corrections, chromatic aberration removal) each press.
 */
@action({ UUID: "com.keelan182.lightroom-presets.toggle-lens-correction" })
export class ToggleLensCorrectionAction extends SingletonAction<ToggleLensCorrectionSettings> {
	constructor(
		private readonly connection: LightroomConnection,
		private readonly developControl: DevelopControlService,
	) {
		super();
	}

	public override async onWillAppear(ev: WillAppearEvent<ToggleLensCorrectionSettings>): Promise<void> {
		if (!ev.action.isKey()) {
			return;
		}
		await ev.action.setTitle(this.computeTitle(ev.payload.settings));
	}

	public override async onKeyDown(ev: KeyDownEvent<ToggleLensCorrectionSettings>): Promise<void> {
		if (!ev.action.isKey()) {
			return;
		}
		const settings = ev.payload.settings;
		const toggle = DEVELOP_TOGGLES.find((t) => t.id === settings.settingId);

		if (!toggle) {
			await ev.action.showAlert();
			await ev.action.setTitle("Select a\nsetting");
			return;
		}

		const nextIsOn = !settings.isOn;

		try {
			await this.developControl.setToggle(toggle.id, nextIsOn ? 1 : 0);
			await ev.action.setSettings({ ...settings, isOn: nextIsOn });
			await ev.action.showOk();
			await ev.action.setTitle(this.computeTitle({ ...settings, isOn: nextIsOn }));
		} catch (err) {
			await ev.action.showAlert();
			const message = err instanceof Error ? err.message : errorMessage(err);
			streamDeck.logger.error(`Toggle ${toggle.id} failed: ${message}`);
			await ev.action.setTitle(err instanceof PresetApplicationError ? shortStatusLabel(err) : "LR Error");
			setTimeout(() => {
				ev.action.setTitle(this.computeTitle(settings)).catch(() => undefined);
			}, 2000);
		}
	}

	private computeTitle(settings: ToggleLensCorrectionSettings): string {
		const toggle = DEVELOP_TOGGLES.find((t) => t.id === settings.settingId);
		if (!toggle) {
			return "Select a\nsetting";
		}
		return `${toggle.label}\n${settings.isOn ? "ON" : "OFF"}`;
	}
}

function shortStatusLabel(err: PresetApplicationError): string {
	switch (err.code) {
		case "not-running":
			return "No\nLightroom";
		case "disconnected":
			return "Not\nConnected";
		case "unresponsive":
			return "No\nResponse";
		default:
			return "LR\nError";
	}
}
