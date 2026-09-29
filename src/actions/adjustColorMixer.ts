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
import {
	colorMixerParameterId,
	COLOR_MIXER_ATTRIBUTES,
	COLOR_MIXER_COLORS,
	type ColorMixerAttribute,
	type ColorMixerColor,
	type DevelopControlService,
} from "../lightroom/developControl.js";
import { PresetApplicationError } from "../lightroom/types.js";

type AdjustColorMixerSettings = {
	color?: ColorMixerColor;
	attribute?: ColorMixerAttribute;
	/** The property inspector's number field writes this as a string even with type="number" - always parse via parseStepOverride(). */
	stepOverride?: number | string;
	indicatorValue?: number;
};

const DEFAULT_STEP = 2;
const DEFAULT_INDICATOR = 50;

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

function isValidColor(value: string | undefined): value is ColorMixerColor {
	return !!value && (COLOR_MIXER_COLORS as readonly string[]).includes(value);
}

function isValidAttribute(value: string | undefined): value is ColorMixerAttribute {
	return !!value && (COLOR_MIXER_ATTRIBUTES as readonly string[]).includes(value);
}

/**
 * "Adjust Color Mixer" - a Stream Deck+ dial (Encoder) action for
 * Lightroom's Color Mixer (HSL) panel: pick one of the 8 color swatches
 * (Red, Orange, Yellow, Green, Aqua, Blue, Purple, Magenta) and one of its
 * three sliders (Hue, Saturation, Luminance), then turn the dial to adjust
 * it - same interaction model as "Adjust Develop Setting"
 * (src/actions/adjustDevelopSetting.ts), just with a color+attribute pair
 * instead of a single flat parameter list, since 8x3 = 24 combinations
 * don't fit well in one dropdown.
 *
 * See DevelopControlService.colorMixerParameterId / docs/PROTOCOL.md for
 * where the underlying `<Attribute>Adjustment<Color>` parameter names come
 * from - unlike most other parameters in this plugin, these were not
 * observed directly in a real External Controller API plugin, only
 * cross-checked against Lightroom's own stable XMP field names.
 */
@action({ UUID: "com.keelan182.lightroom-presets.adjust-color-mixer" })
export class AdjustColorMixerAction extends SingletonAction<AdjustColorMixerSettings> {
	constructor(
		private readonly connection: LightroomConnection,
		private readonly developControl: DevelopControlService,
	) {
		super();
	}

	public override async onWillAppear(ev: WillAppearEvent<AdjustColorMixerSettings>): Promise<void> {
		if (!ev.action.isDial()) {
			return;
		}
		await ev.action.setFeedbackLayout("$B1");
		await this.renderIdle(ev.action, ev.payload.settings);
	}

	public override async onDidReceiveSettings(ev: DidReceiveSettingsEvent<AdjustColorMixerSettings>): Promise<void> {
		if (!ev.action.isDial()) {
			return;
		}
		await this.renderIdle(ev.action, ev.payload.settings);
	}

	public override async onDialRotate(ev: DialRotateEvent<AdjustColorMixerSettings>): Promise<void> {
		const settings = ev.payload.settings;

		if (!isValidColor(settings.color) || !isValidAttribute(settings.attribute)) {
			await ev.action.setFeedback({ title: "Select a\ncolor + slider", value: "" });
			return;
		}

		const parameterId = colorMixerParameterId(settings.color, settings.attribute);
		const label = `${settings.color}: ${settings.attribute}`;
		const step = parseStepOverride(settings.stepOverride) ?? DEFAULT_STEP;
		const coarse = ev.payload.pressed ? 5 : 1;
		const delta = ev.payload.ticks * step * coarse;

		const nextIndicator = clamp((settings.indicatorValue ?? DEFAULT_INDICATOR) + ev.payload.ticks * 4, 0, 100);
		await ev.action.setSettings({ ...settings, indicatorValue: nextIndicator });

		try {
			await this.developControl.adjustParameter(parameterId, delta);
			await ev.action.setFeedback({
				title: label,
				value: `${delta > 0 ? "+" : ""}${delta.toFixed(2)}${ev.payload.pressed ? " (coarse)" : ""}`,
				indicator: { value: nextIndicator },
			});
		} catch (err) {
			const message = err instanceof PresetApplicationError ? shortStatusLabel(err) : "Error";
			streamDeck.logger.error(`Color Mixer dial adjust failed for ${parameterId}: ${err instanceof Error ? err.message : errorMessage(err)}`);
			await ev.action.setFeedback({ title: label, value: message, indicator: { value: nextIndicator } });
		}
	}

	public override async onDialDown(ev: DialDownEvent<AdjustColorMixerSettings>): Promise<void> {
		// Recenters the cosmetic indicator only - see the identical note in
		// AdjustDevelopSettingAction.onDialDown.
		const settings = { ...ev.payload.settings, indicatorValue: DEFAULT_INDICATOR };
		await ev.action.setSettings(settings);
		await this.renderIdle(ev.action, settings);
	}

	private async renderIdle(action: DialAction<AdjustColorMixerSettings>, settings: AdjustColorMixerSettings): Promise<void> {
		const ready = isValidColor(settings.color) && isValidAttribute(settings.attribute);
		await action.setFeedback({
			title: ready ? `${settings.color}: ${settings.attribute}` : "Select a\ncolor + slider",
			value: ready ? "Turn to adjust" : "",
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
