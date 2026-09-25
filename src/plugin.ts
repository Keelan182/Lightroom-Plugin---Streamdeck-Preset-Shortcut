import streamDeck from "@elgato/streamdeck";

import { AdjustDevelopSettingAction } from "./actions/adjustDevelopSetting.js";
import { ApplyPresetAction } from "./actions/applyPreset.js";
import { CopyEditSettingsAction } from "./actions/copyEditSettings.js";
import { DevelopUtilityAction } from "./actions/developUtility.js";
import { FlagAndRateAction } from "./actions/flagAndRate.js";
import { PasteEditSettingsAction } from "./actions/pasteEditSettings.js";
import { RefreshPresetsAction } from "./actions/refreshPresets.js";
import { ToggleLensCorrectionAction } from "./actions/toggleLensCorrection.js";
import { LightroomConnection } from "./lightroom/connection.js";
import { DevelopControlService } from "./lightroom/developControl.js";
import { PresetApplicationService } from "./lightroom/presetApplication.js";
import { PresetManager } from "./lightroom/presetManager.js";

streamDeck.logger.setLevel("info");

const log = (level: "info" | "warn" | "error" | "debug", message: string): void => {
	streamDeck.logger[level](message);
};

const lightroomConnection = new LightroomConnection(log);
const presetManager = new PresetManager(lightroomConnection, log);
const presetApplicationService = new PresetApplicationService(lightroomConnection, presetManager, log);
const developControlService = new DevelopControlService(lightroomConnection, log);

const applyPresetAction = new ApplyPresetAction(lightroomConnection, presetManager, presetApplicationService);
const refreshPresetsAction = new RefreshPresetsAction(lightroomConnection, presetManager, applyPresetAction);
const adjustDevelopSettingAction = new AdjustDevelopSettingAction(lightroomConnection, developControlService);
const toggleLensCorrectionAction = new ToggleLensCorrectionAction(lightroomConnection, developControlService);
const flagAndRateAction = new FlagAndRateAction(lightroomConnection, developControlService);
const developUtilityAction = new DevelopUtilityAction(lightroomConnection, developControlService);
const copyEditSettingsAction = new CopyEditSettingsAction(lightroomConnection, developControlService);
const pasteEditSettingsAction = new PasteEditSettingsAction(lightroomConnection, developControlService);

streamDeck.actions.registerAction(applyPresetAction);
streamDeck.actions.registerAction(refreshPresetsAction);
streamDeck.actions.registerAction(adjustDevelopSettingAction);
streamDeck.actions.registerAction(toggleLensCorrectionAction);
streamDeck.actions.registerAction(flagAndRateAction);
streamDeck.actions.registerAction(developUtilityAction);
streamDeck.actions.registerAction(copyEditSettingsAction);
streamDeck.actions.registerAction(pasteEditSettingsAction);

// Property inspectors open after any earlier "status" event may have fired,
// so push a snapshot the moment one appears rather than leaving it stuck on
// its initial "Checking connection…" placeholder.
streamDeck.ui.onDidAppear(() => {
	streamDeck.ui.sendToPropertyInspector({ event: "connectionStatus", status: lightroomConnection.getStatus() }).catch(() => undefined);
});

lightroomConnection.on("status", (status) => {
	applyPresetAction.refreshTitlesForStatus(status).catch((err) => streamDeck.logger.error(`Failed to refresh titles: ${String(err)}`));
	streamDeck.ui.sendToPropertyInspector({ event: "connectionStatus", status }).catch(() => undefined);

	if (status === "connected") {
		// A fresh connection (first launch, Lightroom relaunch, or reconnect
		// after being closed) may mean our cached ids are stale or empty;
		// refresh automatically so buttons "just work" without the user
		// having to remember to press "Refresh Lightroom Presets" first.
		presetManager
			.refresh()
			.then(({ removedIds }) => applyPresetAction.reconcileAssignments(removedIds))
			.catch((err) => streamDeck.logger.warn(`Automatic preset refresh after connect failed: ${String(err)}`));
	}
});

async function main(): Promise<void> {
	await presetManager.loadCacheFromDisk();
	streamDeck.connect();
	await lightroomConnection.start();
}

main().catch((err) => streamDeck.logger.error(`Plugin failed to start: ${String(err)}`));
