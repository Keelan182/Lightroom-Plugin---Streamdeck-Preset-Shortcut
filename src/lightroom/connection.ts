import { execFile } from "node:child_process";
import { EventEmitter } from "node:events";
import { promises as fs } from "node:fs";
import { randomUUID } from "node:crypto";
import { promisify } from "node:util";
import WebSocket from "ws";

import { getAppSupportDirectory, getConnectionStatePath, getLightroomConnectionsDirectory } from "./paths.js";
import type { ConnectionStateFile, LightroomConnectionStatus, LightroomResponseMessage } from "./types.js";

const execFileAsync = promisify(execFile);

const APP_NAME = "Stream Deck Lightroom Presets";
const APP_VERSION = "1.0.0";
const DEFAULT_HOST = "127.0.0.1";
const DEFAULT_PORT = 7682;

/** Lightroom's own name for the process, as seen in Activity Monitor on macOS. */
const LIGHTROOM_PROCESS_PATTERN = "Adobe Lightroom";

const REQUEST_TIMEOUT_MS = 8000;
const REGISTER_TIMEOUT_MS = 12000; // Longer: the user may need time to click "Pair" in Lightroom.
const POLL_INTERVAL_MS = 3000;
const BACKOFF_START_MS = 1000;
const BACKOFF_MAX_MS = 30000;

interface PendingRequest {
	resolve: (value: LightroomResponseMessage) => void;
	reject: (reason: Error) => void;
	timer: NodeJS.Timeout;
}

export interface LightroomConnectionEvents {
	status: [LightroomConnectionStatus, LightroomConnectionStatus];
}

/**
 * Owns a single, persistent WebSocket connection to Lightroom Desktop/CC's
 * local "External Controller API" and exposes a small request/response API
 * on top of it. Reconnection, pairing (register) and liveness are all
 * handled here so the rest of the plugin never has to think about sockets.
 */
export class LightroomConnection extends EventEmitter {
	private socket: WebSocket | undefined;
	private status: LightroomConnectionStatus = "not-running";
	private readonly pending = new Map<string, PendingRequest>();
	private clientGuid: string | undefined;
	private pollTimer: NodeJS.Timeout | undefined;
	private lastAttemptAt = 0;
	private backoffMs = BACKOFF_START_MS;
	private connecting = false;
	private host = DEFAULT_HOST;
	private port = DEFAULT_PORT;
	private stateLoaded = false;

	constructor(private readonly log: (level: "info" | "warn" | "error" | "debug", message: string) => void = () => {}) {
		super();
	}

	public getStatus(): LightroomConnectionStatus {
		return this.status;
	}

	public configureEndpoint(host?: string, port?: number): void {
		this.host = host && host.trim().length > 0 ? host.trim() : DEFAULT_HOST;
		this.port = port && Number.isFinite(port) && port > 0 ? port : DEFAULT_PORT;
	}

	/** Begins the connect/poll loop. Safe to call once during plugin startup. */
	public async start(): Promise<void> {
		if (this.pollTimer) {
			return;
		}
		await this.loadState();
		await this.detectPort();
		this.pollTimer = setInterval(() => {
			this.tick().catch((err) => this.log("error", `Connection poll loop failed: ${errorMessage(err)}`));
		}, POLL_INTERVAL_MS);
		// Kick off immediately instead of waiting for the first interval tick.
		void this.tick();
	}

	public stop(): void {
		if (this.pollTimer) {
			clearInterval(this.pollTimer);
			this.pollTimer = undefined;
		}
		this.closeSocket("plugin stopping");
	}

	/**
	 * Sends a command to Lightroom and awaits the correlated response.
	 * Throws if not currently connected - callers should check
	 * {@link getStatus} first to give better user-facing errors.
	 */
	public async sendRequest(message: string, params: unknown[] = [], timeoutMs = REQUEST_TIMEOUT_MS): Promise<LightroomResponseMessage> {
		if (!this.socket || this.socket.readyState !== WebSocket.OPEN || this.status !== "connected") {
			throw new Error(`Cannot send "${message}": Lightroom is not connected (status: ${this.status})`);
		}

		const requestId = randomUUID();
		const payload = JSON.stringify({ requestId, object: null, message, params });

		return new Promise<LightroomResponseMessage>((resolve, reject) => {
			const timer = setTimeout(() => {
				this.pending.delete(requestId);
				reject(new Error(`Timed out waiting for Lightroom to respond to "${message}"`));
			}, timeoutMs);

			this.pending.set(requestId, { resolve, reject, timer });

			this.socket?.send(payload, (err) => {
				if (err) {
					clearTimeout(timer);
					this.pending.delete(requestId);
					reject(err);
				}
			});
		});
	}

	private async tick(): Promise<void> {
		const running = await this.isLightroomRunning();

		if (!running) {
			this.closeSocket("Lightroom is not running");
			this.setStatus("not-running");
			this.backoffMs = BACKOFF_START_MS;
			return;
		}

		if (this.status === "connected" || this.connecting) {
			return;
		}

		const now = Date.now();
		if (now - this.lastAttemptAt < this.backoffMs) {
			return;
		}

		this.lastAttemptAt = now;
		await this.attemptConnect();
	}

	private async attemptConnect(): Promise<void> {
		this.connecting = true;
		this.setStatus("connecting");

		const socket = new WebSocket(`ws://${this.host}:${this.port}`);
		this.socket = socket;

		const openedOrFailed = new Promise<boolean>((resolve) => {
			socket.once("open", () => resolve(true));
			socket.once("error", (err) => {
				this.log("debug", `Lightroom socket error: ${errorMessage(err)}`);
				resolve(false);
			});
		});

		socket.on("message", (data) => this.handleMessage(data));
		socket.on("close", () => this.handleClose());
		socket.on("error", () => {
			/* handled via the once("error") above for the initial connect race */
		});

		const opened = await openedOrFailed;
		if (!opened) {
			this.connecting = false;
			this.setStatus("disconnected");
			this.increaseBackoff();
			return;
		}

		try {
			const response = await this.register();
			this.connecting = false;

			if (response.success) {
				if (Array.isArray(response.response) && typeof response.response[0] === "string") {
					this.clientGuid = response.response[0] as string;
					void this.persistState();
				}
				this.setStatus("connected");
				this.backoffMs = BACKOFF_START_MS;
				this.log("info", "Registered with Lightroom's External Controller API");
			} else {
				this.setStatus("unresponsive");
				this.increaseBackoff();
				this.log("warn", "Lightroom rejected the registration request");
			}
		} catch (err) {
			this.connecting = false;
			this.setStatus("unresponsive");
			this.increaseBackoff();
			this.log(
				"warn",
				`Lightroom did not answer the pairing handshake in time (${errorMessage(err)}). If a "Pair" dialog is open in Lightroom, click Allow.`,
			);
		}
	}

	private async register(): Promise<LightroomResponseMessage> {
		const requestId = randomUUID();
		const payload = JSON.stringify({
			requestId,
			object: null,
			message: "register",
			params: [APP_NAME, APP_VERSION, this.clientGuid ?? null],
		});

		return new Promise<LightroomResponseMessage>((resolve, reject) => {
			const timer = setTimeout(() => {
				this.pending.delete(requestId);
				reject(new Error("register timed out"));
			}, REGISTER_TIMEOUT_MS);

			this.pending.set(requestId, { resolve, reject, timer });
			this.socket?.send(payload, (err) => {
				if (err) {
					clearTimeout(timer);
					this.pending.delete(requestId);
					reject(err);
				}
			});
		});
	}

	private handleMessage(data: WebSocket.RawData): void {
		let parsed: LightroomResponseMessage;
		try {
			parsed = JSON.parse(data.toString()) as LightroomResponseMessage;
		} catch {
			this.log("warn", `Received non-JSON message from Lightroom: ${truncate(data.toString())}`);
			return;
		}

		if (parsed.requestId && this.pending.has(parsed.requestId)) {
			const request = this.pending.get(parsed.requestId)!;
			this.pending.delete(parsed.requestId);
			clearTimeout(request.timer);
			request.resolve(parsed);
			return;
		}

		this.log("debug", `Unsolicited message from Lightroom: ${truncate(JSON.stringify(parsed))}`);
	}

	private handleClose(): void {
		if (this.status === "connected") {
			this.log("warn", "Lost connection to Lightroom");
		}
		for (const [id, request] of this.pending) {
			clearTimeout(request.timer);
			request.reject(new Error("Connection to Lightroom closed"));
			this.pending.delete(id);
		}
		this.connecting = false;
		if (this.status !== "not-running") {
			this.setStatus("disconnected");
			this.increaseBackoff();
		}
	}

	private closeSocket(reason: string): void {
		if (this.socket) {
			this.log("debug", `Closing Lightroom socket: ${reason}`);
			this.socket.removeAllListeners();
			if (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING) {
				this.socket.close();
			}
			this.socket = undefined;
		}
		for (const [id, request] of this.pending) {
			clearTimeout(request.timer);
			request.reject(new Error(reason));
			this.pending.delete(id);
		}
	}

	private increaseBackoff(): void {
		this.backoffMs = Math.min(this.backoffMs * 2, BACKOFF_MAX_MS);
	}

	private setStatus(next: LightroomConnectionStatus): void {
		const previous = this.status;
		if (previous === next) {
			return;
		}
		this.status = next;
		this.log("info", `Lightroom connection status: ${previous} -> ${next}`);
		this.emit("status", next, previous);
	}

	/**
	 * macOS-only, read-only process check (no shell, fixed argv - not
	 * susceptible to injection). Used purely to distinguish "Lightroom isn't
	 * open" from "Lightroom is open but unreachable" for clearer error
	 * messages; never used to control or automate Lightroom.
	 */
	private async isLightroomRunning(): Promise<boolean> {
		if (process.platform !== "darwin") {
			return false;
		}
		try {
			// "-f" substring-matches the full command line rather than requiring an
			// exact process-name match, since Adobe's exact process name has not
			// been verified on-device for this build (see docs/TROUBLESHOOTING.md).
			await execFileAsync("pgrep", ["-f", LIGHTROOM_PROCESS_PATTERN]);
			return true;
		} catch {
			return false;
		}
	}

	private async loadState(): Promise<void> {
		if (this.stateLoaded) {
			return;
		}
		this.stateLoaded = true;
		try {
			const raw = await fs.readFile(getConnectionStatePath(), "utf8");
			const state = JSON.parse(raw) as ConnectionStateFile;
			this.clientGuid = state.clientGuid;
		} catch {
			// No prior state; first run.
		}
	}

	private async persistState(): Promise<void> {
		try {
			await fs.mkdir(getAppSupportDirectory(), { recursive: true });
			const state: ConnectionStateFile = { clientGuid: this.clientGuid };
			await fs.writeFile(getConnectionStatePath(), JSON.stringify(state, null, 2), "utf8");
		} catch (err) {
			this.log("warn", `Failed to persist Lightroom pairing state: ${errorMessage(err)}`);
		}
	}

	/**
	 * Best-effort scan of Lightroom's own connections folder for a
	 * non-default port. Adobe does not document this file's schema, so any
	 * failure here silently keeps the default 127.0.0.1:7682.
	 */
	private async detectPort(): Promise<void> {
		try {
			const dir = getLightroomConnectionsDirectory();
			const entries = await fs.readdir(dir);
			const candidate = entries.find((name) => name.toLowerCase().endsWith(".json"));
			if (!candidate) {
				return;
			}
			const raw = await fs.readFile(`${dir}/${candidate}`, "utf8");
			const data: unknown = JSON.parse(raw);
			const port = extractPort(data);
			if (port) {
				this.log("info", `Discovered External Controller API port ${port} from Lightroom's connections folder`);
				this.port = port;
			}
		} catch {
			// Fall back to the documented default port; this is expected on most systems.
		}
	}
}

function extractPort(data: unknown): number | undefined {
	if (data === null || typeof data !== "object") {
		return undefined;
	}
	const record = data as Record<string, unknown>;
	for (const key of ["port", "Port", "websocketPort", "webSocketPort"]) {
		const value = record[key];
		if (typeof value === "number" && Number.isFinite(value)) {
			return value;
		}
	}
	return undefined;
}

function truncate(text: string, max = 300): string {
	return text.length > max ? `${text.slice(0, max)}…` : text;
}

export function errorMessage(err: unknown): string {
	if (err instanceof Error) {
		return err.message;
	}
	return String(err);
}
