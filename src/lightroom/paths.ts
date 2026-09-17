import os from "node:os";
import path from "node:path";

const APP_SUPPORT_DIR_NAME = "com.keelan182.lightroom-presets";

/**
 * Per-user, macOS-appropriate directory for this plugin's own persisted data
 * (preset cache, pairing state). Kept outside the .sdPlugin bundle so it
 * survives plugin updates/reinstalls.
 */
export function getAppSupportDirectory(): string {
	return path.join(os.homedir(), "Library", "Application Support", APP_SUPPORT_DIR_NAME);
}

export function getPresetsCachePath(): string {
	return path.join(getAppSupportDirectory(), "presets-cache.json");
}

export function getConnectionStatePath(): string {
	return path.join(getAppSupportDirectory(), "connection-state.json");
}

/**
 * Best-effort location of the folder Lightroom itself writes connection
 * bookkeeping into. Adobe does not publish a schema for this file, so it is
 * only ever used as an optional hint for discovering a non-default port -
 * the plugin always falls back to the documented default (127.0.0.1:7682)
 * when this can't be read or parsed.
 */
export function getLightroomConnectionsDirectory(): string {
	return path.join(os.homedir(), "Library", "Application Support", "Adobe", "Lightroom CC", "Connections");
}
