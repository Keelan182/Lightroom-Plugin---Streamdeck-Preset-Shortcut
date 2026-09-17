// Generates every PNG icon this plugin ships, from scratch, with no image
// dependencies and no network access. Re-run with `npm run icons` any time
// you want to tweak colors/shapes below.
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { Canvas } from "./png.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SD_PLUGIN_DIR = path.join(__dirname, "..", "com.keelan182.lightroom-presets.sdPlugin");

const PALETTE = {
	presetPurple: [111, 76, 219, 255],
	presetPurpleDark: [79, 53, 168, 255],
	refreshTeal: [22, 163, 148, 255],
	refreshTealDark: [15, 118, 108, 255],
	white: [255, 255, 255, 255],
	white70: [255, 255, 255, 178],
	transparent: [255, 255, 255, 0],
};

async function writePng(canvas, relativePath) {
	const absolute = path.join(SD_PLUGIN_DIR, relativePath);
	await mkdir(path.dirname(absolute), { recursive: true });
	await writeFile(absolute, canvas.toPngBuffer());
	console.log(`wrote ${relativePath} (${canvas.width}x${canvas.height})`);
}

/** A rounded-square app-icon background, matching Stream Deck's own key art conventions. */
function background(size, colorTop, colorBottom) {
	const canvas = new Canvas(size, size);
	// Plain vertical gradient fill first (opaque, ignores corners)...
	for (let y = 0; y < size; y++) {
		const t = y / size;
		const color = lerpColor(colorTop, colorBottom, t);
		canvas.fillRect(0, y, size, y + 1, color);
	}
	// ...then clip the corners to a rounded rect in one pass over the whole canvas.
	canvas.clipToRoundedRect(size * 0.22);
	return canvas;
}

function lerpColor(a, b, t) {
	return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t, 255];
}

/** Abstract "adjustment dial" glyph: an outer ring with a filled center dot and a single tick mark. */
function drawPresetGlyph(canvas, cx, cy, r, color) {
	canvas.annulus(cx, cy, r * 0.72, r, color);
	canvas.fillCircle(cx, cy, r * 0.32, color);
	// Tick mark showing the dial has a "setting", like a preset value.
	const angle = -Math.PI / 2.6;
	const x0 = cx + Math.cos(angle) * r * 0.86;
	const y0 = cy + Math.sin(angle) * r * 0.86;
	const x1 = cx + Math.cos(angle) * r * 1.18;
	const y1 = cy + Math.sin(angle) * r * 1.18;
	canvas.drawThickLine(x0, y0, x1, y1, Math.max(1, r * 0.16), color);
}

/** Circular refresh-arrows glyph. */
function drawRefreshGlyph(canvas, cx, cy, r, thickness, color) {
	const gap = Math.PI * 0.28;
	canvas.annulus(cx, cy, r - thickness, r, color, -Math.PI / 2 + gap / 2, Math.PI * 1.5 - gap / 2);

	const headAngle = Math.PI * 1.5 - gap / 2;
	const headX = cx + Math.cos(headAngle) * (r - thickness / 2);
	const headY = cy + Math.sin(headAngle) * (r - thickness / 2);
	const outward = headAngle + Math.PI / 2;
	const along = headAngle;
	const size = thickness * 1.6;
	const p1 = [headX + Math.cos(along) * size, headY + Math.sin(along) * size];
	const p2 = [headX + Math.cos(outward) * size * 0.8, headY + Math.sin(outward) * size * 0.8];
	const p3 = [headX - Math.cos(outward) * size * 0.8, headY - Math.sin(outward) * size * 0.8];
	canvas.fillTriangle([p1, p2, p3], color);
}

function drawCheckmark(canvas, cx, cy, size, thickness, color) {
	canvas.drawThickLine(cx - size * 0.5, cy, cx - size * 0.12, cy + size * 0.4, thickness, color);
	canvas.drawThickLine(cx - size * 0.12, cy + size * 0.4, cx + size * 0.55, cy - size * 0.35, thickness, color);
}

function drawWarningTriangle(canvas, cx, cy, size, fillColor, markColor) {
	const h = size * 0.9;
	const points = [
		[cx, cy - h * 0.62],
		[cx - size * 0.58, cy + h * 0.42],
		[cx + size * 0.58, cy + h * 0.42],
	];
	canvas.fillTriangle(points, fillColor);
	canvas.drawThickLine(cx, cy - h * 0.18, cx, cy + h * 0.08, size * 0.09, markColor);
	canvas.fillCircle(cx, cy + h * 0.24, size * 0.055, markColor);
}

async function generateApplyPresetIcons() {
	for (const [size, suffix] of [
		[20, ""],
		[40, "@2x"],
	]) {
		const canvas = background(size, PALETTE.presetPurple, PALETTE.presetPurpleDark);
		drawPresetGlyph(canvas, size / 2, size / 2, size * 0.3, PALETTE.white);
		await writePng(canvas, `imgs/actions/apply-preset/icon${suffix}.png`);
	}

	for (const [size, suffix] of [
		[72, ""],
		[144, "@2x"],
	]) {
		const canvas = background(size, PALETTE.presetPurple, PALETTE.presetPurpleDark);
		drawPresetGlyph(canvas, size / 2, size * 0.42, size * 0.24, PALETTE.white);
		await writePng(canvas, `imgs/actions/apply-preset/key${suffix}.png`);
	}
}

async function generateRefreshPresetIcons() {
	for (const [size, suffix] of [
		[20, ""],
		[40, "@2x"],
	]) {
		const canvas = background(size, PALETTE.refreshTeal, PALETTE.refreshTealDark);
		drawRefreshGlyph(canvas, size / 2, size / 2, size * 0.3, Math.max(1.5, size * 0.09), PALETTE.white);
		await writePng(canvas, `imgs/actions/refresh-presets/icon${suffix}.png`);
	}

	for (const [size, suffix] of [
		[72, ""],
		[144, "@2x"],
	]) {
		const canvas = background(size, PALETTE.refreshTeal, PALETTE.refreshTealDark);
		drawRefreshGlyph(canvas, size / 2, size * 0.42, size * 0.24, Math.max(2, size * 0.09), PALETTE.white);
		await writePng(canvas, `imgs/actions/refresh-presets/key${suffix}.png`);
	}
}

async function generateCategoryIcon() {
	// Category/action-list icons are rendered by Stream Deck as a template
	// (white-on-transparent), so this is intentionally monochrome.
	for (const [size, suffix] of [
		[28, ""],
		[56, "@2x"],
	]) {
		const canvas = new Canvas(size, size);
		drawPresetGlyph(canvas, size / 2, size / 2, size * 0.36, PALETTE.white);
		await writePng(canvas, `imgs/plugin/category-icon${suffix}.png`);
	}
}

async function generateMarketplaceIcon() {
	for (const [size, suffix] of [
		[288, ""],
		[576, "@2x"],
	]) {
		const canvas = background(size, PALETTE.presetPurple, PALETTE.presetPurpleDark);
		drawPresetGlyph(canvas, size / 2, size / 2, size * 0.3, PALETTE.white);
		await writePng(canvas, `imgs/plugin/marketplace${suffix}.png`);
	}
}

async function generateStateOverlays() {
	// Standalone overlay art referenced from docs/TROUBLESHOOTING.md and
	// usable as custom "success"/"error" icons via Stream Deck's own image
	// picker if a user wants to assign them manually to a multi-state action.
	const size = 144;

	const ok = new Canvas(size, size);
	ok.fillCircle(size / 2, size / 2, size * 0.46, [45, 163, 92, 255]);
	drawCheckmark(ok, size / 2, size / 2, size * 0.42, size * 0.09, PALETTE.white);
	await writePng(ok, "imgs/plugin/status-connected.png");

	const warn = new Canvas(size, size);
	drawWarningTriangle(warn, size / 2, size / 2 + size * 0.05, size * 0.78, [219, 148, 40, 255], [46, 30, 5, 255]);
	await writePng(warn, "imgs/plugin/status-disconnected.png");

	const err = new Canvas(size, size);
	drawWarningTriangle(err, size / 2, size / 2 + size * 0.05, size * 0.78, [199, 62, 62, 255], PALETTE.white);
	await writePng(err, "imgs/plugin/status-error.png");
}

await generateApplyPresetIcons();
await generateRefreshPresetIcons();
await generateCategoryIcon();
await generateMarketplaceIcon();
await generateStateOverlays();

console.log("Icon generation complete.");
