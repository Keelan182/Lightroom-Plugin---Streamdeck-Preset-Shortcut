/**
 * Connection state between this plugin and Adobe Lightroom Desktop/CC's local
 * External Controller API (ws://127.0.0.1:7682 by default).
 *
 * - not-running: the Lightroom process could not be found on this Mac.
 * - connecting: a socket handshake ("register") is currently in flight.
 * - connected: registered successfully; requests can be sent.
 * - disconnected: Lightroom is running but the socket could not be opened or
 *   dropped (most commonly because "Enable external controllers" is off).
 * - unresponsive: the socket opened but Lightroom never answered the
 *   register/request handshake in time (e.g. an unanswered pairing dialog).
 */
export type LightroomConnectionStatus = "not-running" | "connecting" | "connected" | "disconnected" | "unresponsive";

export interface LightroomPreset {
	/** Stable identifier Lightroom assigns to the preset. */
	id: string;
	/** Human readable preset name as shown in Lightroom's Presets panel. */
	name: string;
}

export interface PresetCacheFile {
	updatedAt: string;
	presets: LightroomPreset[];
}

export interface ConnectionStateFile {
	/** Client GUID handed back by Lightroom during "register"; resending it lets Lightroom recognise a previously paired client. */
	clientGuid?: string;
}

export type PluginGlobalSettings = {
	favoritePresetIds?: string[];
	websocketHost?: string;
	websocketPort?: number;
};

export type TitleMode = "preset" | "custom" | "preset-and-status";

export type ApplyPresetSettings = {
	presetId?: string;
	presetName?: string;
	titleMode?: TitleMode;
	customTitle?: string;
};

/** Errors surfaced to the action layer so button feedback and logs can be specific. */
export type PresetApplicationErrorCode =
	| "not-running"
	| "disconnected"
	| "unresponsive"
	| "preset-not-found"
	| "no-preset-configured"
	| "lightroom-error";

export class PresetApplicationError extends Error {
	public readonly code: PresetApplicationErrorCode;

	constructor(code: PresetApplicationErrorCode, message: string) {
		super(message);
		this.name = "PresetApplicationError";
		this.code = code;
	}
}

/** A single JSON message exchanged with Lightroom's External Controller API. */
export interface LightroomRequestMessage {
	requestId: string;
	object: null;
	message: string;
	params: unknown[];
}

export interface LightroomResponseMessage {
	requestId?: string;
	success?: boolean;
	response?: unknown;
	error?: unknown;
}
