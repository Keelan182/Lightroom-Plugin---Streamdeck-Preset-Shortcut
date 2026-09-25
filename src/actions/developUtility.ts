import streamDeck, {
	action,
	type DidReceiveSettingsEvent,
	type KeyDownEvent,
	SingletonAction,
	type WillAppearEvent,
} from "@elgato/streamdeck";

import { errorMessage, type LightroomConnection } from "../lightroom/connection.js";
import { DEVELOP_COMMANDS, type DevelopControlService } from "../lightroom/developControl.js";

const UTILITY_COMMAND_IDS = new Set(["resetAllDevelopAdjustments", "copyEditSettings", "pasteEditSettings"]);

type DevelopUtilitySettings = {
	commandId?: string;
};

/**
 * "Develop Utility" - the three parameter-less Develop workflow commands
 * that don't fit "apply a preset" or "flag/rate": reset every adjustment,
 * and copy/paste the whole edit-settings stack between photos.
 */
@action({ UUID: "com.keelan182.lightroom-presets.develop-utility" })
export class DevelopUtilityAction extends SingletonAction<DevelopUtilitySettings> {
	constructor(
		private readonly connection: LightroomConnection,
		private readonly developControl: DevelopControlService,
	) {
		super();
	}

	public override async onWillAppear(ev: WillAppearEvent<DevelopUtilitySettings>): Promise<void> {
		if (!ev.action.isKey()) {
			return;
		}
		await ev.action.setTitle(this.computeTitle(ev.payload.settings));
	}

	public override async onDidReceiveSettings(ev: DidReceiveSettingsEvent<DevelopUtilitySettings>): Promise<void> {
		if (!ev.action.isKey()) {
			return;
		}
		await ev.action.setTitle(this.computeTitle(ev.payload.settings));
	}

	public override async onKeyDown(ev: KeyDownEvent<DevelopUtilitySettings>): Promise<void> {
		if (!ev.action.isKey()) {
			return;
		}
		const commandId = ev.payload.settings.commandId;
		if (!commandId || !UTILITY_COMMAND_IDS.has(commandId)) {
			await ev.action.showAlert();
			await ev.action.setTitle("Select an\naction");
			return;
		}

		try {
			await this.developControl.sendCommand(commandId);
			await ev.action.showOk();
		} catch (err) {
			await ev.action.showAlert();
			const message = err instanceof Error ? err.message : errorMessage(err);
			streamDeck.logger.error(`Command ${commandId} failed: ${message}`);
		}
	}

	private computeTitle(settings: DevelopUtilitySettings): string {
		const command = DEVELOP_COMMANDS.find((c) => c.id === settings.commandId);
		return command ? command.label : "Select an\naction";
	}
}
