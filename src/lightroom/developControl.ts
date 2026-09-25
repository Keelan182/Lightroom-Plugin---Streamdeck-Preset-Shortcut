import type { LightroomConnection } from "./connection.js";
import { errorMessage } from "./connection.js";
import { PresetApplicationError } from "./types.js";

/**
 * A continuously-adjustable Develop parameter, controllable via
 * "increment"/"decrement" on Lightroom's External Controller API. The `id`
 * values below are Lightroom's own internal Develop setting names (observed
 * from a real third-party plugin for this same API - see
 * docs/PROTOCOL.md - not invented). `defaultStep` mirrors sensible defaults
 * for each parameter's usual range.
 */
export interface DevelopParameter {
	id: string;
	label: string;
	group: "Light" | "Color" | "Effects" | "Detail";
	defaultStep: number;
}

export const DEVELOP_PARAMETERS: DevelopParameter[] = [
	{ id: "Exposure2012", label: "Exposure", group: "Light", defaultStep: 0.1 },
	{ id: "Contrast2012", label: "Contrast", group: "Light", defaultStep: 2 },
	{ id: "Highlights2012", label: "Highlights", group: "Light", defaultStep: 2 },
	{ id: "Shadows2012", label: "Shadows", group: "Light", defaultStep: 2 },
	{ id: "Whites2012", label: "Whites", group: "Light", defaultStep: 2 },
	{ id: "Blacks2012", label: "Blacks", group: "Light", defaultStep: 2 },
	{ id: "Temperature", label: "White Balance: Temperature", group: "Color", defaultStep: 50 },
	{ id: "Tint", label: "White Balance: Tint", group: "Color", defaultStep: 1 },
	{ id: "Vibrance", label: "Vibrance", group: "Color", defaultStep: 2 },
	{ id: "Saturation", label: "Saturation", group: "Color", defaultStep: 2 },
	{ id: "Texture", label: "Texture", group: "Effects", defaultStep: 2 },
	{ id: "Clarity2012", label: "Clarity", group: "Effects", defaultStep: 2 },
	{ id: "Dehaze", label: "Dehaze", group: "Effects", defaultStep: 2 },
	{ id: "Sharpness", label: "Sharpening", group: "Detail", defaultStep: 2 },
	{ id: "LuminanceSmoothing", label: "Noise Reduction: Luminance", group: "Detail", defaultStep: 2 },
	{ id: "ColorNoiseReduction", label: "Noise Reduction: Color", group: "Detail", defaultStep: 2 },
];

/** An on/off Develop setting, set via "setValue" with 0 or 1 - not readable back, only settable (see docs/PROTOCOL.md). */
export interface DevelopToggle {
	id: string;
	label: string;
}

export const DEVELOP_TOGGLES: DevelopToggle[] = [
	{ id: "LensProfileEnable", label: "Lens Profile Corrections" },
	{ id: "AutoLateralCA", label: "Remove Chromatic Aberration" },
];

/** A single fire-and-forget Lightroom command with no parameters. */
export interface DevelopCommand {
	id: string;
	label: string;
	group: "Flag" | "Rating" | "Color Label" | "Utility";
}

export const DEVELOP_COMMANDS: DevelopCommand[] = [
	{ id: "flagPick", label: "Flag: Pick", group: "Flag" },
	{ id: "flagReject", label: "Flag: Reject", group: "Flag" },
	{ id: "flagUnflag", label: "Flag: Remove Flag", group: "Flag" },
	{ id: "rating0", label: "Rating: 0 stars", group: "Rating" },
	{ id: "rating1", label: "Rating: 1 star", group: "Rating" },
	{ id: "rating2", label: "Rating: 2 stars", group: "Rating" },
	{ id: "rating3", label: "Rating: 3 stars", group: "Rating" },
	{ id: "rating4", label: "Rating: 4 stars", group: "Rating" },
	{ id: "rating5", label: "Rating: 5 stars", group: "Rating" },
	{ id: "colorLabelRed", label: "Color Label: Red", group: "Color Label" },
	{ id: "colorLabelYellow", label: "Color Label: Yellow", group: "Color Label" },
	{ id: "colorLabelGreen", label: "Color Label: Green", group: "Color Label" },
	{ id: "colorLabelBlue", label: "Color Label: Blue", group: "Color Label" },
	{ id: "colorLabelPurple", label: "Color Label: Purple", group: "Color Label" },
	{ id: "colorLabelNone", label: "Color Label: None", group: "Color Label" },
	{ id: "resetAllDevelopAdjustments", label: "Reset All Develop Adjustments", group: "Utility" },
	{ id: "copyEditSettings", label: "Copy Edit Settings", group: "Utility" },
	{ id: "pasteEditSettings", label: "Paste Edit Settings", group: "Utility" },
];

function requireConnected(connection: LightroomConnection, verb: string): void {
	const status = connection.getStatus();
	if (status === "not-running") {
		throw new PresetApplicationError("not-running", "Lightroom is not running. Open Lightroom Desktop and try again.");
	}
	if (status === "disconnected") {
		throw new PresetApplicationError(
			"disconnected",
			"Unable to connect to Lightroom. Check Lightroom's External Controller settings (Preferences > Interface).",
		);
	}
	if (status === "unresponsive") {
		throw new PresetApplicationError("unresponsive", "Lightroom is not responding. If a pairing dialog is open in Lightroom, click Allow.");
	}
	void verb;
}

/**
 * Sends continuous adjustments, toggle values, and one-shot commands to
 * Lightroom's Develop module. Kept separate from PresetApplicationService
 * since presets and live Develop-parameter control are different concerns
 * that happen to share the same connection - see docs/ARCHITECTURE.md.
 */
export class DevelopControlService {
	constructor(
		private readonly connection: LightroomConnection,
		private readonly log: (level: "info" | "warn" | "error" | "debug", message: string) => void = () => {},
	) {}

	/**
	 * Applies a single relative adjustment. `amount` may be positive
	 * (increment) or negative (decrement); its magnitude is the amount to
	 * change by, in Lightroom's own units for that parameter (e.g. whole
	 * stops for Exposure are ~1.0, Temperature is in Kelvin).
	 */
	public async adjustParameter(parameterId: string, amount: number): Promise<void> {
		requireConnected(this.connection, "adjust");
		if (amount === 0) {
			return;
		}
		const command = amount > 0 ? "increment" : "decrement";
		try {
			await this.connection.sendRequest(command, [parameterId, Math.abs(amount)]);
		} catch (err) {
			this.log("error", `${command} ${parameterId} by ${Math.abs(amount)} failed: ${errorMessage(err)}`);
			throw new PresetApplicationError("lightroom-error", `Lightroom did not confirm adjusting ${parameterId}.`);
		}
	}

	/** Sets a 0/1-valued Develop setting. There is no way to read the current value back - see docs/PROTOCOL.md. */
	public async setToggle(parameterId: string, value: 0 | 1): Promise<void> {
		requireConnected(this.connection, "set");
		try {
			await this.connection.sendRequest("setValue", [parameterId, value]);
		} catch (err) {
			this.log("error", `setValue ${parameterId}=${value} failed: ${errorMessage(err)}`);
			throw new PresetApplicationError("lightroom-error", `Lightroom did not confirm setting ${parameterId}.`);
		}
	}

	/** Sends a fire-and-forget command (flagging, rating, color labels, reset/copy/paste). */
	public async sendCommand(commandId: string): Promise<void> {
		requireConnected(this.connection, "run");
		try {
			await this.connection.sendRequest(commandId);
		} catch (err) {
			this.log("error", `command ${commandId} failed: ${errorMessage(err)}`);
			throw new PresetApplicationError("lightroom-error", `Lightroom did not confirm running ${commandId}.`);
		}
	}
}
