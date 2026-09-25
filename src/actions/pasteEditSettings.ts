import streamDeck, { action, type KeyDownEvent, SingletonAction } from "@elgato/streamdeck";

import { errorMessage, type LightroomConnection } from "../lightroom/connection.js";
import type { DevelopControlService } from "../lightroom/developControl.js";

/**
 * "Paste Edit Settings" - a single, unconfigurable button that pastes
 * whatever was last copied with "Copy Edit Settings" onto the currently
 * selected photo. Kept as its own action for the same reason as
 * CopyEditSettingsAction - a zero-configuration drag-and-drop shortcut.
 */
@action({ UUID: "com.keelan182.lightroom-presets.paste-edit-settings" })
export class PasteEditSettingsAction extends SingletonAction<Record<string, never>> {
	constructor(
		private readonly connection: LightroomConnection,
		private readonly developControl: DevelopControlService,
	) {
		super();
	}

	public override async onKeyDown(ev: KeyDownEvent<Record<string, never>>): Promise<void> {
		if (!ev.action.isKey()) {
			return;
		}

		try {
			await this.developControl.sendCommand("pasteEditSettings");
			await ev.action.showOk();
		} catch (err) {
			await ev.action.showAlert();
			streamDeck.logger.error(`Paste edit settings failed: ${err instanceof Error ? err.message : errorMessage(err)}`);
		}
	}
}
