import type { LightroomConnection } from "./connection.js";
import { errorMessage } from "./connection.js";
import type { PresetManager } from "./presetManager.js";
import { PresetApplicationError } from "./types.js";

/**
 * Applies a cached preset id to whatever photo is currently selected in
 * Lightroom. Kept separate from {@link LightroomConnection} so the
 * connection layer only knows about the wire protocol, while this layer
 * knows about preset-specific validation and user-facing error mapping.
 */
export class PresetApplicationService {
	constructor(
		private readonly connection: LightroomConnection,
		private readonly presetManager: PresetManager,
		private readonly log: (level: "info" | "warn" | "error" | "debug", message: string) => void = () => {},
	) {}

	public async apply(presetId: string | undefined): Promise<void> {
		if (!presetId) {
			throw new PresetApplicationError("no-preset-configured", "No preset is configured for this button yet.");
		}

		const status = this.connection.getStatus();
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
			throw new PresetApplicationError(
				"unresponsive",
				"Lightroom is not responding. If a pairing dialog is open in Lightroom, click Allow.",
			);
		}

		const known = this.presetManager.findById(presetId);
		if (!known) {
			throw new PresetApplicationError(
				"preset-not-found",
				`Preset not found: ${presetId}. Open the action settings and select a preset, or run "Refresh Lightroom Presets".`,
			);
		}

		this.log("info", `Applying preset "${known.name}" (${presetId})`);

		try {
			const response = await this.connection.sendRequest("applyPreset", [presetId]);
			if (response.success === false) {
				throw new PresetApplicationError("lightroom-error", `Lightroom rejected applyPreset for "${known.name}"`);
			}
			this.log("info", `Preset "${known.name}" applied`);
		} catch (err) {
			if (err instanceof PresetApplicationError) {
				throw err;
			}
			this.log("error", `applyPreset failed for "${known.name}": ${errorMessage(err)}`);
			throw new PresetApplicationError("lightroom-error", `Lightroom did not confirm applying "${known.name}": ${errorMessage(err)}`);
		}
	}
}
