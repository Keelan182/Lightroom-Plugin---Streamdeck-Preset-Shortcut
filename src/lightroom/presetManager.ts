import { promises as fs } from "node:fs";

import type { LightroomConnection } from "./connection.js";
import { errorMessage } from "./connection.js";
import { getAppSupportDirectory, getPresetsCachePath } from "./paths.js";
import type { LightroomPreset, PresetCacheFile } from "./types.js";

const NAME_FETCH_CONCURRENCY = 4;
const NAME_FETCH_STAGGER_MS = 15;

export interface RefreshResult {
	presets: LightroomPreset[];
	removedIds: string[];
}

/**
 * Discovers, caches and resolves Lightroom develop presets.
 *
 * Lightroom's External Controller API only exposes a flat list of preset ids
 * plus a name-per-id lookup - there is no folder/group metadata available
 * over this API, so no hierarchy is reconstructed here (see
 * docs/ARCHITECTURE.md for the confirmed limitation).
 */
export class PresetManager {
	private presets: LightroomPreset[] = [];
	private loadedFromDisk = false;

	constructor(
		private readonly connection: LightroomConnection,
		private readonly log: (level: "info" | "warn" | "error" | "debug", message: string) => void = () => {},
	) {}

	public async loadCacheFromDisk(): Promise<void> {
		if (this.loadedFromDisk) {
			return;
		}
		this.loadedFromDisk = true;
		try {
			const raw = await fs.readFile(getPresetsCachePath(), "utf8");
			const cache = JSON.parse(raw) as PresetCacheFile;
			this.presets = cache.presets ?? [];
			this.log("info", `Loaded ${this.presets.length} cached presets from disk (last refreshed ${cache.updatedAt})`);
		} catch {
			this.log("info", "No cached preset list found on disk yet; run \"Refresh Lightroom Presets\" once Lightroom is connected.");
		}
	}

	public getPresets(): LightroomPreset[] {
		return this.presets;
	}

	public findById(id: string): LightroomPreset | undefined {
		return this.presets.find((preset) => preset.id === id);
	}

	public search(query: string): LightroomPreset[] {
		const needle = query.trim().toLowerCase();
		if (!needle) {
			return this.presets;
		}
		return this.presets.filter((preset) => preset.name.toLowerCase().includes(needle));
	}

	/**
	 * Re-discovers every preset from Lightroom: retrieves ids via
	 * "getPresetIDs", resolves each id's name via "getPresetName", caches the
	 * result to disk, and reports which previously-known ids disappeared so
	 * the caller can flag stale button assignments.
	 */
	public async refresh(): Promise<RefreshResult> {
		this.log("info", "Requesting preset list from Lightroom (getPresetIDs)");
		const idsResponse = await this.connection.sendRequest("getPresetIDs");
		const ids = extractPresetIds(idsResponse.response);
		this.log("info", `Lightroom reported ${ids.length} preset id(s); resolving names`);

		const previousIds = new Set(this.presets.map((preset) => preset.id));
		const resolved: LightroomPreset[] = [];

		for (let start = 0; start < ids.length; start += NAME_FETCH_CONCURRENCY) {
			const batch = ids.slice(start, start + NAME_FETCH_CONCURRENCY);
			const names = await Promise.all(
				batch.map(async (id) => {
					try {
						const nameResponse = await this.connection.sendRequest("getPresetName", [id]);
						const name = extractPresetName(nameResponse.response);
						return name ? { id, name } : undefined;
					} catch (err) {
						this.log("warn", `Failed to resolve name for preset ${id}: ${errorMessage(err)}`);
						return undefined;
					}
				}),
			);
			for (const preset of names) {
				if (preset) {
					resolved.push(preset);
				}
			}
			if (start + NAME_FETCH_CONCURRENCY < ids.length) {
				await sleep(NAME_FETCH_STAGGER_MS);
			}
		}

		resolved.sort((a, b) => a.name.localeCompare(b.name));
		this.presets = resolved;

		const currentIds = new Set(resolved.map((preset) => preset.id));
		const removedIds = [...previousIds].filter((id) => !currentIds.has(id));

		await this.saveCacheToDisk();
		this.log("info", `Preset refresh complete: ${resolved.length} preset(s) cached, ${removedIds.length} removed since last refresh`);

		return { presets: resolved, removedIds };
	}

	private async saveCacheToDisk(): Promise<void> {
		try {
			await fs.mkdir(getAppSupportDirectory(), { recursive: true });
			const cache: PresetCacheFile = { updatedAt: new Date().toISOString(), presets: this.presets };
			await fs.writeFile(getPresetsCachePath(), JSON.stringify(cache, null, 2), "utf8");
		} catch (err) {
			this.log("error", `Failed to write preset cache to disk: ${errorMessage(err)}`);
		}
	}
}

/**
 * Lightroom's "getPresetIDs" response has been observed to arrive as a
 * direct array of id strings, a JSON-encoded string containing that array,
 * an object wrapping the array in an unpredictable property name, or a
 * single nested array-of-arrays. This defensively unwraps all of those
 * shapes down to a flat string[].
 */
export function extractPresetIds(raw: unknown): string[] {
	const arrays = unwrapToArrays(raw);
	const ids: string[] = [];
	for (const value of arrays) {
		if (typeof value === "string" && value.length > 0) {
			ids.push(value);
		}
	}
	return ids;
}

export function extractPresetName(raw: unknown): string | undefined {
	if (typeof raw === "string") {
		return raw;
	}
	if (Array.isArray(raw) && typeof raw[0] === "string") {
		return raw[0];
	}
	return undefined;
}

function unwrapToArrays(raw: unknown): unknown[] {
	if (typeof raw === "string") {
		try {
			return unwrapToArrays(JSON.parse(raw));
		} catch {
			return [];
		}
	}
	if (Array.isArray(raw)) {
		return raw.flatMap((item) => (Array.isArray(item) ? unwrapToArrays(item) : [item]));
	}
	if (raw !== null && typeof raw === "object") {
		for (const value of Object.values(raw as Record<string, unknown>)) {
			if (Array.isArray(value)) {
				return unwrapToArrays(value);
			}
		}
	}
	return [];
}

function sleep(ms: number): Promise<void> {
	return new Promise((resolve) => setTimeout(resolve, ms));
}
