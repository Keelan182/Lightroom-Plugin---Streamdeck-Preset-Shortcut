import streamDeck, { action, type DidReceiveSettingsEvent, type KeyDownEvent, SingletonAction, type WillAppearEvent } from "@elgato/streamdeck";

import { errorMessage, type LightroomConnection } from "../lightroom/connection.js";
import { DEVELOP_COMMANDS, type DevelopControlService } from "../lightroom/developControl.js";
import { PresetApplicationError } from "../lightroom/types.js";

type FlagAndRateSettings = {
	commandId?: string;
};

/**
 * "Flag & Rate Photo" - fires one of Lightroom's flag/rating/color-label
 * commands. These are fire-and-forget on the wire (see docs/PROTOCOL.md):
 * Lightroom doesn't confirm the photo was actually flagged/rated, only that
 * the command was accepted, so success feedback here means "Lightroom
 * acknowledged the request", not "verified applied to a selected photo".
 */
@action({ UUID: "com.keelan182.lightroom-presets.flag-and-rate" })
export class FlagAndRateAction extends SingletonAction<FlagAndRateSettings> {
	constructor(
		private readonly connection: LightroomConnection,
		private readonly developControl: DevelopControlService,
	) {
		super();
	}

	public override async onWillAppear(ev: WillAppearEvent<FlagAndRateSettings>): Promise<void> {
		if (!ev.action.isKey()) {
			return;
		}
		await ev.action.setTitle(this.computeTitle(ev.payload.settings));
	}

	public override async onDidReceiveSettings(ev: DidReceiveSettingsEvent<FlagAndRateSettings>): Promise<void> {
		if (!ev.action.isKey()) {
			return;
		}
		await ev.action.setTitle(this.computeTitle(ev.payload.settings));
	}

	public override async onKeyDown(ev: KeyDownEvent<FlagAndRateSettings>): Promise<void> {
		if (!ev.action.isKey()) {
			return;
		}
		const command = DEVELOP_COMMANDS.find((c) => c.id === ev.payload.settings.commandId);

		if (!command) {
			await ev.action.showAlert();
			await ev.action.setTitle("Select an\naction");
			return;
		}

		try {
			await this.developControl.sendCommand(command.id);
			await ev.action.showOk();
		} catch (err) {
			await ev.action.showAlert();
			const message = err instanceof Error ? err.message : errorMessage(err);
			streamDeck.logger.error(`Command ${command.id} failed: ${message}`);
		}
	}

	private computeTitle(settings: FlagAndRateSettings): string {
		const command = DEVELOP_COMMANDS.find((c) => c.id === settings.commandId);
		return command ? command.label : "Select an\naction";
	}
}
