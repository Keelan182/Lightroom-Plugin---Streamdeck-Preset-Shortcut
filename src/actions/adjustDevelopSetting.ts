import streamDeck, {
	action,
	type DialAction,
	type DialDownEvent,
	type DialRotateEvent,
	type DidReceiveSettingsEvent,
	SingletonAction,
	type WillAppearEvent,
} from "@elgato/streamdeck";

import { errorMessage, type LightroomConnection } from "../lightroom/connection.js";
import { DEVELOP_PARAMETERS, type DevelopControlService } from "../lightroom/developControl.js";
import { PresetApplicationError } from "../lightroom/types.js";

type AdjustDevelopSettingSettings = {
	parameterId?: string;
	/** The property inspector's number field writes this as a string even with type="number" - always parse via parseStepOverride(). */
	stepOverride?: number | string;
	indicatorValue?: number;
};

function parseStepOverride(value: number | string | undefined): number | undefined {
	if (typeof value === "number") {
		return Number.isFinite(value) && value > 0 ? value : undefined;
	}
	if (typeof value === "string" && value.trim().length > 0) {
		const parsed = Number(value);
		return Number.isFinite(parsed) && parsed > 0 ? parsed : undefined;
	}
	return undefined;
}

const DEFAULT_INDICATOR = 50;

/**
 * "Adjust Develop Setting" - a Stream Deck+ dial (Encoder) action. Rotating
 * the dial sends a single batched "increment"/"decrement" request to
 * Lightroom sized by however many ticks were turned, rather than one
 * request per tick (an improvement over the reference plugin studied for
 * this project - see docs/PROTOCOL.md). Holding the dial down while turning
 * applies a 5x coarser step, using the SDK's own `pressed` flag on the
 * rotate event - no extra state needed.
 *
 * The touch strip cannot show Lightroom's actual current value - the
 * External Controller API has no "get current value" command (see
 * docs/PROTOCOL.md) - so it shows the parameter name and the delta just
 * sent, plus a cosmetic position indicator that resets when you tap the
 * touch strip. It does not reflect Lightroom's real slider position.
 */
@action({ UUID: "com.keelan182.lightroom-presets.adjust-develop-setting" })
export class AdjustDevelopSettingAction extends SingletonAction<AdjustDevelopSettingSettings> {
	constructor(
		private readonly connection: LightroomConnection,
		private readonly developControl: DevelopControlService,
	) {
		super();
	}

	public override async onWillAppear(ev: WillAppearEvent<AdjustDevelopSettingSettings>): Promise<void> {
		if (!ev.action.isDial()) {
			return;
		}
		await ev.action.setFeedbackLayout("$B1");
		await this.renderIdle(ev.action, ev.payload.settings);
	}

	public override async onDidReceiveSettings(ev: DidReceiveSettingsEvent<AdjustDevelopSettingSettings>): Promise<void> {
		if (!ev.action.isDial()) {
			return;
		}
		await this.renderIdle(ev.action, ev.payload.settings);
	}

	public override async onDialRotate(ev: DialRotateEvent<AdjustDevelopSettingSettings>): Promise<void> {
		const settings = ev.payload.settings;
		const parameter = DEVELOP_PARAMETERS.find((p) => p.id === settings.parameterId);

		if (!parameter) {
			await ev.action.setFeedback({ title: "Select a\nparameter", value: "" });
			return;
		}

		const step = parseStepOverride(settings.stepOverride) ?? parameter.defaultStep;
		const coarse = ev.payload.pressed ? 5 : 1;
		const delta = ev.payload.ticks * step * coarse;

		const nextIndicator = clamp((settings.indicatorValue ?? DEFAULT_INDICATOR) + ev.payload.ticks * 4, 0, 100);
		await ev.action.setSettings({ ...settings, indicatorValue: nextIndicator });

		try {
			await this.developControl.adjustParameter(parameter.id, delta);
			await ev.action.setFeedback({
				title: parameter.label,
				value: `${delta > 0 ? "+" : ""}${delta.toFixed(2)}${ev.payload.pressed ? " (coarse)" : ""}`,
				indicator: { value: nextIndicator },
			});
		} catch (err) {
			const message = err instanceof PresetApplicationError ? shortStatusLabel(err) : "Error";
			streamDeck.logger.error(`Dial adjust failed for ${parameter.id}: ${err instanceof Error ? err.message : errorMessage(err)}`);
			await ev.action.setFeedback({ title: parameter.label, value: message, indicator: { value: nextIndicator } });
		}
	}

	public override async onDialDown(ev: DialDownEvent<AdjustDevelopSettingSettings>): Promise<void> {
		// Recenters the cosmetic indicator only - Lightroom's own value is
		// untouched, since there is no "reset this one parameter" command
		// (only resetAllDevelopAdjustments, which resets everything - see
		// the "Develop Utility" action).
		const settings = { ...ev.payload.settings, indicatorValue: DEFAULT_INDICATOR };
		await ev.action.setSettings(settings);
		await this.renderIdle(ev.action, settings);
	}

	private async renderIdle(action: DialAction<AdjustDevelopSettingSettings>, settings: AdjustDevelopSettingSettings): Promise<void> {
		const parameter = DEVELOP_PARAMETERS.find((p) => p.id === settings.parameterId);
		await action.setFeedback({
			title: parameter ? parameter.label : "Select a\nparameter",
			value: parameter ? "Turn to adjust" : "",
			indicator: { value: settings.indicatorValue ?? DEFAULT_INDICATOR },
		});
	}
}

function clamp(value: number, min: number, max: number): number {
	return Math.max(min, Math.min(max, value));
}

function shortStatusLabel(err: PresetApplicationError): string {
	switch (err.code) {
		case "not-running":
			return "No Lightroom";
		case "disconnected":
			return "Not Connected";
		case "unresponsive":
			return "No Response";
		default:
			return "LR Error";
	}
}
