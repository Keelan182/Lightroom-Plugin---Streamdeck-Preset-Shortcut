import streamDeck, { action, type KeyDownEvent, SingletonAction } from "@elgato/streamdeck";

import { errorMessage, type LightroomConnection } from "../lightroom/connection.js";
import type { DevelopControlService } from "../lightroom/developControl.js";

/**
 * "Copy Edit Settings" - a single, unconfigurable button that copies the
 * whole edit-settings stack from the currently selected photo, ready for
 * "Paste Edit Settings" on another photo. Kept as its own action (rather
 * than only living inside the "Develop Utility" dropdown) so it's a
 * zero-configuration drag-and-drop shortcut.
 */
@action({ UUID: "com.keelan182.lightroom-presets.copy-edit-settings" })
export class CopyEditSettingsAction extends SingletonAction<Record<string, never>> {
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
			await this.developControl.sendCommand("copyEditSettings");
			await ev.action.showOk();
		} catch (err) {
			await ev.action.showAlert();
			streamDeck.logger.error(`Copy edit settings failed: ${err instanceof Error ? err.message : errorMessage(err)}`);
		}
	}
}
