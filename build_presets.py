#!/usr/bin/env python3
"""Build "Iconic Film Stocks" presets for Lightroom (cloud-based desktop app,
formerly "Lightroom CC"; NOT Lightroom Classic).

Source of truth for traits: ./film_stocks.txt (RTF content, read-only).
Every trait quoted in STOCKS below is checked verbatim against that file.

Output (all presets in ONE folder and ONE Lightroom group):
    output/Iconic Film Stocks/<Preset Name>.xmp
    output/Iconic Film Stocks.zip
    output/README.md

Run:  python3 build_presets.py
Standard library only.
"""

import re
import shutil
import sys
import uuid
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "film_stocks.txt"
OUT = ROOT / "output"
COLLECTION = "Iconic Film Stocks"
TREE = OUT / COLLECTION
# Every preset uses this one crs:Group so the whole set stays together in
# Lightroom's Presets panel. The film family is kept in each Description.
GROUP = COLLECTION
ZIP_PATH = OUT / f"{COLLECTION}.zip"

# No reference/sample.xmp was supplied, so these follow the current Camera Raw
# settings schema. Process Version 6 shipped with Camera Raw 15.4 (June 2023)
# and is written as ProcessVersion="15.4"; it reduces banding in the Color
# Mixer and B&W Mixer, which these presets lean on heavily.
CRS_VERSION = "15.4"
PROCESS_VERSION = "15.4"

NS_X = "adobe:ns:meta/"
NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
NS_CRS = "http://ns.adobe.com/camera-raw-settings/1.0/"

HSL_CHANNELS = ("Red", "Orange", "Yellow", "Green", "Aqua", "Blue", "Purple", "Magenta")

# --------------------------------------------------------------------------
# Small constructors so every stock definition is complete and explicit.
# --------------------------------------------------------------------------


def basic(contrast, highlights, shadows, whites, blacks, sat=0, vib=0, exposure=None):
    d = {"Contrast2012": contrast, "Highlights2012": highlights, "Shadows2012": shadows,
         "Whites2012": whites, "Blacks2012": blacks, "Saturation": sat, "Vibrance": vib}
    if exposure is not None:
        d["Exposure2012"] = exposure
    return d


def fx(clarity, texture, dehaze):
    return {"Clarity2012": clarity, "Texture": texture, "Dehaze": dehaze}


def hsl(**ch):
    """hsl(Red=(hue, sat, lum), ...) - all 8 channels required."""
    assert set(ch) == set(HSL_CHANNELS), f"HSL needs all 8 channels, got {sorted(ch)}"
    d = {}
    for c in HSL_CHANNELS:
        h, s, l = ch[c]
        d[f"HueAdjustment{c}"] = h
        d[f"SaturationAdjustment{c}"] = s
        d[f"LuminanceAdjustment{c}"] = l
    return d


def mixer(**ch):
    """B&W Mixer: spectral sensitivity per channel - all 8 required."""
    assert set(ch) == set(HSL_CHANNELS), f"GrayMixer needs all 8 channels, got {sorted(ch)}"
    return {f"GrayMixer{c}": ch[c] for c in HSL_CHANNELS}


def grade(sh=(0, 0, 0), mid=(0, 0, 0), hi=(0, 0, 0), glob=(0, 0, 0), blend=50, balance=0):
    """Color Grading. Shadows/highlights hue+sat live in the SplitToning* keys
    (reused by Color Grading since ACR 13); luminance and midtone/global use
    ColorGrade* keys. Tuples are (hue 0-359, sat 0-100, lum -100..100)."""
    return {
        "SplitToningShadowHue": sh[0], "SplitToningShadowSaturation": sh[1], "ColorGradeShadowLum": sh[2],
        "ColorGradeMidtoneHue": mid[0], "ColorGradeMidtoneSat": mid[1], "ColorGradeMidtoneLum": mid[2],
        "SplitToningHighlightHue": hi[0], "SplitToningHighlightSaturation": hi[1], "ColorGradeHighlightLum": hi[2],
        "ColorGradeGlobalHue": glob[0], "ColorGradeGlobalSat": glob[1], "ColorGradeGlobalLum": glob[2],
        "ColorGradeBlending": blend, "SplitToningBalance": balance,
    }


def cal(shadow_tint=0, red_hue=0, red_sat=0, green_hue=0, green_sat=0, blue_hue=0, blue_sat=0):
    return {"ShadowTint": shadow_tint, "RedHue": red_hue, "RedSaturation": red_sat,
            "GreenHue": green_hue, "GreenSaturation": green_sat,
            "BlueHue": blue_hue, "BlueSaturation": blue_sat}


def grain(amount, size, roughness):
    return {"GrainAmount": amount, "GrainSize": size, "GrainFrequency": roughness}


def sharpen(amount, radius, detail, masking):
    return {"Sharpness": amount, "SharpenRadius": radius, "SharpenDetail": detail,
            "SharpenEdgeMasking": masking}


def vignette(amount=0, midpoint=50, feather=50, roundness=0):
    # Style 1 = Highlight Priority (Lightroom's default post-crop style).
    return {"PostCropVignetteAmount": amount, "PostCropVignetteMidpoint": midpoint,
            "PostCropVignetteFeather": feather, "PostCropVignetteRoundness": roundness,
            "PostCropVignetteStyle": 1, "PostCropVignetteHighlightContrast": 0}


LINEAR = [(0, 0), (255, 255)]


def curves(master, red=LINEAR, green=LINEAR, blue=LINEAR):
    return {"master": master, "red": red, "green": green, "blue": blue}


# --------------------------------------------------------------------------
# Stock definitions. "map" pairs a trait quoted verbatim from film_stocks.txt
# (or a bracketed derived note, e.g. ISO differentiation) with the crs keys
# that implement it; the README table is rendered from these pairs using the
# real values, so the documentation cannot drift from the presets.
# --------------------------------------------------------------------------

STOCKS = [
    # ------------------------------------------------------------ slide ---
    dict(
        family="Kodachrome", name="Kodachrome 25", iso=25, kind="color", category="Color slide",
        basic=basic(25, -15, -5, 6, -16, sat=8, vib=5),
        fx=fx(8, 12, 0),
        curves=curves([(0, 0), (64, 54), (128, 128), (192, 204), (255, 252)],
                      red=[(0, 0), (128, 132), (255, 255)], blue=[(0, 0), (128, 124), (255, 250)]),
        hsl=hsl(Red=(0, 20, -8), Orange=(-4, 10, 0), Yellow=(-6, 18, -5), Green=(12, -10, -10),
                Aqua=(5, -10, 0), Blue=(-5, 5, -12), Purple=(0, -10, 0), Magenta=(0, -5, 0)),
        grade=grade(sh=(20, 5, 0), hi=(45, 8, 0)),
        cal=cal(red_hue=6, red_sat=10, green_hue=-5, blue_hue=-8, blue_sat=10),
        grain=grain(8, 12, 35), sharpen=sharpen(55, 0.9, 35, 10), vignette=vignette(-8, 50, 70),
        map=[("Deep, rich reds and yellows", ["SaturationAdjustmentRed", "SaturationAdjustmentYellow", "RedSaturation", "HueAdjustmentYellow"]),
             ("strong contrast", ["Contrast2012", "Blacks2012", "curve"]),
             ('"warm but crisp" rendering', ["red", "blue", "SplitToningHighlightHue", "SplitToningHighlightSaturation", "Texture"]),
             ("[ISO 25: finest grain and highest acutance of the three]", ["GrainAmount", "Sharpness"])],
        notes="Best on daylight scenes with strong primaries. Lower Amount for skin-heavy portraits.",
        limits=["K-14's specific dye response and archival stability cannot be reproduced with sliders; this is a tonal/colour approximation."],
    ),
    dict(
        family="Kodachrome", name="Kodachrome 64", iso=64, kind="color", category="Color slide",
        basic=basic(22, -15, -3, 5, -14, sat=7, vib=6),
        fx=fx(8, 10, 0),
        curves=curves([(0, 0), (64, 56), (128, 128), (192, 202), (255, 252)],
                      red=[(0, 0), (128, 133), (255, 255)], green=[(0, 0), (128, 129), (255, 255)],
                      blue=[(0, 0), (128, 123), (255, 248)]),
        hsl=hsl(Red=(-3, 22, -6), Orange=(-5, 12, 2), Yellow=(-8, 20, -4), Green=(10, -8, -8),
                Aqua=(5, -8, 0), Blue=(-6, 8, -10), Purple=(0, -10, 0), Magenta=(-3, -5, 0)),
        grade=grade(sh=(25, 6, 0), hi=(42, 10, 0)),
        cal=cal(red_hue=8, red_sat=12, green_hue=-6, blue_hue=-8, blue_sat=8),
        grain=grain(14, 16, 40), sharpen=sharpen(50, 1.0, 30, 10), vignette=vignette(-8, 50, 70),
        map=[("Deep, rich reds and yellows", ["SaturationAdjustmentRed", "SaturationAdjustmentYellow", "RedSaturation", "HueAdjustmentOrange"]),
             ("strong contrast", ["Contrast2012", "Blacks2012", "curve"]),
             ('"warm but crisp" rendering', ["red", "green", "blue", "SplitToningHighlightHue", "SplitToningHighlightSaturation"]),
             ("Associated with National Geographic", ["[warmest highlights of the family]"]),
             ("[ISO 64: slightly more grain than 25]", ["GrainAmount"])],
        notes="The 'National Geographic' variant. Great for travel and street colour.",
        limits=["K-14 dye response approximated; no grain-structure or dye-cloud emulation beyond Lightroom Grain."],
    ),
    dict(
        family="Kodachrome", name="Kodachrome 200", iso=200, kind="color", category="Color slide",
        basic=basic(18, -12, 0, 4, -10, sat=4, vib=5),
        fx=fx(6, 4, 0),
        curves=curves([(0, 4), (64, 58), (128, 129), (192, 200), (255, 250)],
                      red=[(0, 0), (128, 134), (255, 255)], green=[(0, 0), (128, 130), (255, 254)],
                      blue=[(0, 0), (128, 121), (255, 246)]),
        hsl=hsl(Red=(-2, 16, -4), Orange=(-4, 10, 2), Yellow=(-10, 14, 0), Green=(8, -12, -6),
                Aqua=(3, -12, 0), Blue=(-4, 2, -8), Purple=(0, -12, 0), Magenta=(-2, -8, 0)),
        grade=grade(sh=(30, 6, 0), mid=(45, 4, 0), hi=(48, 10, 0)),
        cal=cal(red_hue=6, red_sat=8, green_hue=-4, blue_hue=-6, blue_sat=4),
        grain=grain(28, 24, 55), sharpen=sharpen(38, 1.0, 25, 10), vignette=vignette(-10, 45, 65),
        map=[("Deep, rich reds and yellows", ["SaturationAdjustmentRed", "SaturationAdjustmentYellow", "RedSaturation"]),
             ("strong contrast", ["Contrast2012", "curve"]),
             ('"warm but crisp" rendering', ["red", "blue", "ColorGradeMidtoneHue", "ColorGradeMidtoneSat"]),
             ("[ISO 200: lower contrast, warmer/yellower, clearly visible grain]", ["Contrast2012", "GrainAmount", "GrainSize"])],
        notes="Grainier, warmer Kodachrome; good for available-light colour.",
        limits=["K-14 dye response approximated."],
    ),
    dict(
        family="Fujifilm Velvia", name="Fujifilm Velvia 50", iso=50, kind="color", category="Color slide",
        basic=basic(35, -20, -8, 10, -25, sat=25, vib=15),
        fx=fx(10, 12, 5),
        curves=curves([(0, 0), (64, 46), (128, 128), (192, 212), (255, 255)]),
        hsl=hsl(Red=(0, 15, -5), Orange=(0, 5, 0), Yellow=(-3, 15, -5), Green=(5, 30, -10),
                Aqua=(0, 20, -8), Blue=(-3, 25, -15), Purple=(5, 15, -5), Magenta=(0, 25, -5)),
        grade=grade(sh=(320, 6, 0), hi=(40, 3, 0)),
        cal=cal(shadow_tint=4, red_sat=10, green_sat=15, blue_sat=25),
        grain=grain(5, 10, 30), sharpen=sharpen(60, 0.8, 40, 15), vignette=vignette(-10, 50, 70),
        map=[("Extreme saturation, especially in greens, blues, and magentas", ["Saturation", "Vibrance", "SaturationAdjustmentGreen", "SaturationAdjustmentBlue", "SaturationAdjustmentMagenta", "BlueSaturation"]),
             ("high contrast and a narrow exposure latitude", ["Contrast2012", "Blacks2012", "curve"]),
             ("Very fine grain at ISO 50", ["GrainAmount", "GrainSize"]),
             ("Can shift warm/magenta in shade", ["SplitToningShadowHue", "SplitToningShadowSaturation", "ShadowTint"])],
        notes="Landscapes. Lower Amount (40-60) for portraits; skin turns hot quickly.",
        limits=["Reciprocity failure on long exposures is exposure-dependent and not emulated."],
    ),
    dict(
        family="Fujifilm Velvia", name="Fujifilm Velvia 100", iso=100, kind="color", category="Color slide",
        basic=basic(30, -18, -5, 8, -20, sat=20, vib=12),
        fx=fx(8, 10, 4),
        curves=curves([(0, 0), (64, 49), (128, 128), (192, 209), (255, 255)]),
        hsl=hsl(Red=(0, 12, -4), Orange=(0, 4, 0), Yellow=(-2, 12, -4), Green=(4, 22, -8),
                Aqua=(0, 16, -6), Blue=(-2, 20, -12), Purple=(4, 12, -4), Magenta=(0, 20, -4)),
        grade=grade(sh=(330, 4, 0)),
        cal=cal(shadow_tint=2, red_sat=8, green_sat=10, blue_sat=20),
        grain=grain(10, 14, 35), sharpen=sharpen(55, 0.9, 35, 15), vignette=vignette(-8, 50, 70),
        map=[("Extreme saturation, especially in greens, blues, and magentas", ["Saturation", "SaturationAdjustmentGreen", "SaturationAdjustmentBlue", "SaturationAdjustmentMagenta"]),
             ("high contrast and a narrow exposure latitude", ["Contrast2012", "Blacks2012"]),
             ("Can shift warm/magenta in shade", ["SplitToningShadowHue", "SplitToningShadowSaturation"]),
             ("[ISO 100: a notch less saturation/contrast than 50, slightly more grain]", ["Saturation", "Contrast2012", "GrainAmount"])],
        notes="Slightly more forgiving Velvia; still lower Amount for people.",
        limits=["Reciprocity behaviour not emulated."],
    ),
    dict(
        family="Fujifilm Provia", name="Fujifilm Provia 100F", iso=100, kind="color", category="Color slide",
        basic=basic(12, -10, 0, 4, -6, sat=5, vib=5),
        fx=fx(4, 8, 0),
        curves=curves([(0, 0), (64, 59), (128, 128), (192, 198), (255, 255)]),
        hsl=hsl(Red=(0, 4, 0), Orange=(0, 0, 2), Yellow=(0, 3, 0), Green=(2, 5, -2),
                Aqua=(0, 4, 0), Blue=(0, 5, -3), Purple=(0, 0, 0), Magenta=(0, 2, 0)),
        grade=grade(),
        cal=cal(blue_sat=5),
        grain=grain(4, 10, 30), sharpen=sharpen(55, 0.8, 40, 15), vignette=vignette(0),
        map=[("Neutral, accurate color with moderate saturation", ["Saturation", "Vibrance", "SaturationAdjustmentBlue", "[no colour grading]"]),
             ("extremely fine grain", ["GrainAmount", "GrainSize"]),
             ('A more "faithful" counterpart to Velvia', ["Contrast2012", "curve"])],
        notes="Neutral all-rounder; good base for product work.",
        limits=[],
    ),
    dict(
        family="Kodak Ektachrome", name="Kodak Ektachrome E100", iso=100, kind="color", category="Color slide",
        basic=basic(15, -12, 0, 5, -8, sat=8, vib=10),
        fx=fx(5, 10, 2),
        curves=curves([(0, 0), (64, 57), (128, 128), (192, 202), (255, 255)],
                      red=[(0, 0), (128, 126), (255, 253)], blue=[(0, 0), (128, 131), (255, 255)]),
        hsl=hsl(Red=(3, 5, 0), Orange=(0, -3, 3), Yellow=(4, 0, 0), Green=(5, 5, -3),
                Aqua=(0, 10, 0), Blue=(-2, 12, -6), Purple=(0, 0, 0), Magenta=(0, 3, 0)),
        grade=grade(sh=(220, 5, 0), hi=(210, 6, 0)),
        cal=cal(blue_sat=8),
        grain=grain(8, 12, 35), sharpen=sharpen(55, 0.9, 35, 12), vignette=vignette(0),
        map=[("Cleaner, cooler, more neutral palette than Kodachrome", ["red", "blue", "SplitToningHighlightHue", "SplitToningShadowHue"]),
             ("slightly blue bias", ["SaturationAdjustmentBlue", "SaturationAdjustmentAqua", "BlueSaturation"]),
             ("Fine grain and good sharpness", ["GrainAmount", "Sharpness", "Texture"])],
        notes="Clean, cool slide look; nice for snow, water and architecture.",
        limits=[],
    ),
    # --------------------------------------------------------- negative ---
    dict(
        family="Kodak Portra", name="Kodak Portra 160", iso=160, kind="color", category="Color negative",
        basic=basic(-12, -28, 15, -10, 10, sat=-10, vib=-4, exposure=0.10),
        fx=fx(-5, -6, 0),
        curves=curves([(0, 14), (64, 70), (128, 130), (192, 194), (255, 246)],
                      red=[(0, 0), (128, 131), (255, 255)], blue=[(0, 3), (128, 127), (255, 252)]),
        hsl=hsl(Red=(0, -10, 0), Orange=(3, -6, 6), Yellow=(-5, -15, 0), Green=(15, -25, 5),
                Aqua=(0, -20, 0), Blue=(-5, -15, 5), Purple=(0, -15, 0), Magenta=(0, -15, 0)),
        grade=grade(sh=(200, 3, 0), hi=(40, 7, 0)),
        cal=cal(red_sat=-4, blue_sat=-5),
        grain=grain(10, 14, 40), sharpen=sharpen(35, 1.0, 25, 25), vignette=vignette(0),
        map=[("Soft contrast, muted pastels", ["Contrast2012", "curve", "Saturation", "SaturationAdjustmentGreen", "SaturationAdjustmentYellow"]),
             ("natural, smooth skin tones", ["HueAdjustmentOrange", "LuminanceAdjustmentOrange", "Clarity2012", "Texture"]),
             ("keeps highlights smooth", ["Highlights2012", "Whites2012", "curve"]),
             ("[ISO 160: lowest contrast/saturation, finest grain of the three]", ["Contrast2012", "Saturation", "GrainAmount"])],
        notes="Portra tolerates 1-2 stops of overexposure: brighten the image first (or shoot it bright), then apply.",
        limits=["Negative-film exposure latitude cannot be added after capture; the highlight roll-off only mimics it."],
    ),
    dict(
        family="Kodak Portra", name="Kodak Portra 400", iso=400, kind="color", category="Color negative",
        basic=basic(-8, -25, 12, -8, 8, sat=-6, vib=-2),
        fx=fx(-3, -4, 0),
        curves=curves([(0, 12), (64, 68), (128, 130), (192, 196), (255, 248)],
                      red=[(0, 0), (128, 132), (255, 255)], blue=[(0, 4), (128, 127), (255, 251)]),
        hsl=hsl(Red=(0, -6, 0), Orange=(4, -4, 5), Yellow=(-6, -12, 0), Green=(14, -20, 4),
                Aqua=(0, -16, 0), Blue=(-5, -12, 4), Purple=(0, -12, 0), Magenta=(0, -12, 0)),
        grade=grade(sh=(195, 4, 0), hi=(40, 8, 0)),
        cal=cal(red_sat=-2, blue_sat=-4),
        grain=grain(18, 20, 45), sharpen=sharpen(35, 1.0, 25, 25), vignette=vignette(0),
        map=[("Soft contrast, muted pastels", ["Contrast2012", "curve", "Saturation", "SaturationAdjustmentGreen"]),
             ("natural, smooth skin tones", ["HueAdjustmentOrange", "LuminanceAdjustmentOrange", "Clarity2012"]),
             ("Very fine grain for its speed", ["GrainAmount", "GrainSize"]),
             ("[ISO 400: a little more contrast, colour and grain than 160]", ["Contrast2012", "Saturation", "GrainAmount"])],
        notes="Most versatile Portra. Overexpose/brighten before applying for the classic airy look.",
        limits=["Exposure latitude not reproducible after capture."],
    ),
    dict(
        family="Kodak Portra", name="Kodak Portra 800", iso=800, kind="color", category="Color negative",
        basic=basic(-4, -22, 10, -6, 5, sat=-2, vib=0),
        fx=fx(0, -2, 0),
        curves=curves([(0, 10), (64, 66), (128, 130), (192, 198), (255, 249)],
                      red=[(0, 0), (128, 133), (255, 255)], blue=[(0, 4), (128, 126), (255, 250)]),
        hsl=hsl(Red=(0, -2, 0), Orange=(4, -2, 4), Yellow=(-6, -8, 0), Green=(12, -15, 3),
                Aqua=(0, -12, 0), Blue=(-4, -8, 3), Purple=(0, -8, 0), Magenta=(0, -8, 0)),
        grade=grade(sh=(195, 5, 0), hi=(38, 10, 0)),
        cal=cal(blue_sat=-2),
        grain=grain(28, 26, 50), sharpen=sharpen(30, 1.1, 20, 25), vignette=vignette(0),
        map=[("Soft contrast, muted pastels", ["Contrast2012", "Saturation"]),
             ("natural, smooth skin tones", ["HueAdjustmentOrange", "LuminanceAdjustmentOrange"]),
             ("Very fine grain for its speed", ["GrainAmount", "GrainSize"]),
             ("[ISO 800: most contrast, colour, warmth and grain of the family]", ["Contrast2012", "SplitToningHighlightSaturation", "GrainAmount"])],
        notes="Low-light/event Portra; warmer highlights.",
        limits=["Exposure latitude not reproducible after capture."],
    ),
    dict(
        family="Kodak Ektar", name="Kodak Ektar 100", iso=100, kind="color", category="Color negative",
        basic=basic(20, -15, 5, 6, -10, sat=18, vib=10),
        fx=fx(8, 15, 3),
        curves=curves([(0, 0), (64, 52), (128, 129), (192, 206), (255, 255)],
                      red=[(0, 0), (128, 132), (255, 255)], blue=[(0, 0), (128, 125), (255, 252)]),
        hsl=hsl(Red=(-3, 20, -5), Orange=(-2, 5, 0), Yellow=(0, 10, 0), Green=(4, 15, -4),
                Aqua=(0, 10, 0), Blue=(-2, 20, -10), Purple=(0, 5, 0), Magenta=(0, 10, 0)),
        grade=grade(glob=(35, 4, 0)),
        cal=cal(red_sat=12, blue_sat=10),
        grain=grain(3, 8, 25), sharpen=sharpen(65, 0.8, 45, 15), vignette=vignette(0),
        map=[("finest-grained color negative films ever made", ["GrainAmount", "GrainSize"]),
             ("very high sharpness", ["Sharpness", "SharpenDetail", "Texture"]),
             ("Saturated, punchy colors with strong reds", ["Saturation", "SaturationAdjustmentRed", "RedSaturation", "Contrast2012"]),
             ("slight warm cast", ["red", "blue", "ColorGradeGlobalHue", "ColorGradeGlobalSat"]),
             ("Less forgiving with skin tones", ["HueAdjustmentRed", "[no skin-protecting orange tweaks]"])],
        notes="Landscape/travel/architecture. Lower Amount for faces.",
        limits=[],
    ),
    dict(
        family="Kodak Gold", name="Kodak Gold 200", iso=200, kind="color", category="Color negative",
        basic=basic(8, -15, 10, 0, 6, sat=5, vib=8),
        fx=fx(0, 0, 0),
        curves=curves([(0, 8), (64, 64), (128, 130), (192, 198), (255, 250)],
                      red=[(0, 0), (128, 134), (255, 255)], green=[(0, 0), (128, 130), (255, 255)],
                      blue=[(0, 0), (128, 118), (255, 240)]),
        hsl=hsl(Red=(3, 5, 0), Orange=(-5, 10, 2), Yellow=(-8, 15, 5), Green=(-10, -10, 0),
                Aqua=(0, -10, 0), Blue=(-5, -10, -5), Purple=(0, -10, 0), Magenta=(0, -5, 0)),
        grade=grade(sh=(35, 8, 0), mid=(45, 10, 0), hi=(50, 15, 0)),
        cal=cal(red_hue=4),
        grain=grain(32, 30, 55), sharpen=sharpen(30, 1.1, 20, 15), vignette=vignette(-10, 45, 60),
        map=[("Warm, golden-yellow cast", ["red", "blue", "SplitToningHighlightHue", "SplitToningHighlightSaturation", "ColorGradeMidtoneHue", "ColorGradeMidtoneSat"]),
             ("medium saturation", ["Saturation", "Vibrance", "SaturationAdjustmentYellow"]),
             ("visible but pleasant grain", ["GrainAmount", "GrainSize", "GrainFrequency"]),
             ('nostalgic, "family photo" look', ["Blacks2012", "curve", "PostCropVignetteAmount"])],
        notes="Summer, family and travel snapshots. Already warm: don't add warmth with WB on top.",
        limits=[],
    ),
    dict(
        family="Fujifilm Pro 400H", name="Fujifilm Pro 400H", iso=400, kind="color", category="Color negative",
        basic=basic(-10, -25, 18, -5, 12, sat=-8, vib=5, exposure=0.15),
        fx=fx(-8, -5, 0),
        curves=curves([(0, 16), (64, 74), (128, 134), (192, 198), (255, 248)],
                      green=[(0, 2), (128, 130), (255, 255)], blue=[(0, 10), (64, 70), (128, 130), (255, 252)]),
        hsl=hsl(Red=(0, -12, 0), Orange=(2, -8, 8), Yellow=(10, -20, 0), Green=(20, -15, 10),
                Aqua=(-5, -10, 10), Blue=(-8, -10, 10), Purple=(0, -15, 0), Magenta=(0, -12, 5)),
        grade=grade(sh=(195, 15, 0), hi=(60, 4, 0)),
        cal=cal(green_hue=5, blue_hue=-10, blue_sat=5),
        grain=grain(20, 20, 45), sharpen=sharpen(35, 1.0, 25, 25), vignette=vignette(0),
        map=[("pastel, airy colors", ["Saturation", "Exposure2012", "Shadows2012", "curve"]),
             ("cool-leaning greens", ["HueAdjustmentGreen", "HueAdjustmentYellow", "GreenHue"]),
             ("cyan-blue shadows", ["blue", "green", "SplitToningShadowHue", "SplitToningShadowSaturation"]),
             ("improved skin-tone", ["LuminanceAdjustmentOrange", "SaturationAdjustmentOrange", "Clarity2012"])],
        notes="Bright, pastel weddings/portraits. Works best on slightly overexposed images.",
        limits=["The fourth colour layer's fluorescent-light behaviour is not emulated."],
    ),
    dict(
        family="Fujifilm Superia", name="Fujifilm Superia 400", iso=400, kind="color", category="Color negative",
        basic=basic(12, -10, 5, 3, -6, sat=12, vib=8),
        fx=fx(5, 4, 0),
        curves=curves([(0, 0), (64, 56), (128, 128), (192, 202), (255, 254)],
                      green=[(0, 0), (128, 130), (255, 255)], blue=[(0, 4), (128, 129), (255, 254)]),
        hsl=hsl(Red=(5, 5, 0), Orange=(2, 0, 0), Yellow=(8, 5, 0), Green=(10, 20, -5),
                Aqua=(0, 10, 0), Blue=(-5, 15, -5), Purple=(0, 5, 0), Magenta=(0, 10, 0)),
        grade=grade(sh=(175, 8, 0), hi=(200, 3, 0)),
        cal=cal(shadow_tint=-4, green_sat=8, blue_sat=8),
        grain=grain(28, 25, 55), sharpen=sharpen(40, 1.0, 25, 15), vignette=vignette(-6, 50, 60),
        map=[("more saturated", ["Saturation", "Vibrance"]),
             ("punchy greens and blues", ["SaturationAdjustmentGreen", "SaturationAdjustmentBlue", "GreenSaturation", "BlueSaturation"]),
             ("slightly cool palette versus Kodak", ["green", "blue", "SplitToningShadowHue", "ShadowTint"])],
        notes="Everyday Fuji consumer look; strong on foliage and skies.",
        limits=[],
    ),
    dict(
        family="CineStill", name="CineStill 800T", iso=800, kind="color", category="Color negative",
        basic=basic(10, -30, 10, 5, -5, sat=5, vib=10),
        fx=fx(-10, -5, -8),
        curves=curves([(0, 6), (64, 58), (128, 128), (192, 204), (255, 250)],
                      red=[(0, 0), (128, 126), (192, 196), (255, 255)], blue=[(0, 6), (128, 134), (255, 250)]),
        hsl=hsl(Red=(-5, 15, 10), Orange=(-8, 10, 5), Yellow=(-10, -10, 0), Green=(30, -20, -5),
                Aqua=(5, 15, 0), Blue=(-10, 15, -10), Purple=(0, -5, 0), Magenta=(0, 5, 0)),
        grade=grade(sh=(190, 20, 0), mid=(200, 10, 0), hi=(20, 15, 5)),
        cal=cal(shadow_tint=-6, red_hue=10, red_sat=10, blue_hue=-15, blue_sat=15),
        grain=grain(35, 30, 50), sharpen=sharpen(30, 1.1, 20, 15), vignette=vignette(-12, 45, 60),
        map=[("renders cool/teal in daylight", ["blue", "SplitToningShadowHue", "SplitToningShadowSaturation", "ColorGradeMidtoneHue", "BlueHue"]),
             ("red-orange halation glow around bright highlights", ["SplitToningHighlightHue", "SplitToningHighlightSaturation", "red", "LuminanceAdjustmentRed", "Dehaze", "Highlights2012"]),
             ("Cinematic night-city aesthetic", ["HueAdjustmentGreen", "Clarity2012", "PostCropVignetteAmount"])],
        notes="Night street, neon and tungsten scenes. Leave white balance as shot; the preset adds the teal cast through grading, not WB.",
        limits=["Halation is a spatial glow around bright sources; Lightroom has no spatial bloom, so it is approximated with warm highlight grading and negative Dehaze/Clarity."],
        weak=True,
    ),
    dict(
        family="Kodak Vision3", name="Kodak Vision3 500T", iso=500, kind="color", category="Color negative",
        basic=basic(5, -25, 12, -4, 4, sat=-2, vib=5),
        fx=fx(-2, -2, 0),
        curves=curves([(0, 10), (64, 64), (128, 128), (192, 196), (255, 248)],
                      blue=[(0, 4), (128, 131), (255, 252)]),
        hsl=hsl(Red=(0, 5, 0), Orange=(-3, 0, 3), Yellow=(-6, -10, 0), Green=(20, -15, -3),
                Aqua=(0, 8, 0), Blue=(-6, 8, -6), Purple=(0, -8, 0), Magenta=(0, 0, 0)),
        grade=grade(sh=(190, 14, 0), mid=(195, 6, 0), hi=(35, 6, 0)),
        cal=cal(shadow_tint=-3, blue_hue=-10, blue_sat=10),
        grain=grain(30, 25, 45), sharpen=sharpen(35, 1.0, 25, 15), vignette=vignette(-6, 50, 65),
        map=[("Motion-picture stock repackaged for stills", ["curve", "Highlights2012", "Shadows2012", "[flat, log-like cinema curve]"]),
             ("Tungsten-balanced, so it renders cool/teal in daylight", ["SplitToningShadowHue", "SplitToningShadowSaturation", "ColorGradeMidtoneHue", "BlueHue"]),
             ("[With remjet intact: no halation, cleaner highlights than CineStill]", ["Dehaze", "SplitToningHighlightSaturation"])],
        notes="Cinematic colour with a long tonal scale; good for dusk and interiors.",
        limits=["ECN-2 print-film interaction is not modelled."],
    ),
    # ------------------------------------------------------------ B & W ---
    dict(
        family="Kodak Tri-X", name="Kodak Tri-X 400", iso=400, kind="bw", category="Black & white",
        basic=basic(35, -10, -10, 15, -20),
        fx=fx(20, 15, 3),
        curves=curves([(0, 0), (64, 48), (128, 130), (192, 212), (255, 255)]),
        mixer=mixer(Red=-5, Orange=0, Yellow=5, Green=-10, Aqua=-10, Blue=5, Purple=5, Magenta=0),
        grain=grain(50, 35, 65), sharpen=sharpen(45, 1.0, 30, 10), vignette=vignette(-10, 50, 60),
        map=[("Prominent grain", ["GrainAmount", "GrainSize", "GrainFrequency"]),
             ("high, punchy contrast", ["Contrast2012", "Blacks2012", "Whites2012", "curve"]),
             ("Gritty, classic documentary look", ["Clarity2012", "Texture"])],
        notes="Street and documentary. Pairs well with deliberately underexposed, contrasty light.",
        limits=["Push-processing (1600-3200) response is not a separate preset; add contrast/grain manually."],
    ),
    dict(
        family="Ilford HP5 Plus", name="Ilford HP5 Plus 400", iso=400, kind="bw", category="Black & white",
        basic=basic(18, -15, 10, 5, -10),
        fx=fx(8, 6, 0),
        curves=curves([(0, 4), (64, 56), (128, 128), (192, 204), (255, 252)]),
        mixer=mixer(Red=0, Orange=5, Yellow=5, Green=-5, Aqua=-5, Blue=8, Purple=5, Magenta=2),
        grain=grain(42, 30, 55), sharpen=sharpen(40, 1.0, 25, 10), vignette=vignette(-6, 50, 60),
        map=[("Smoother tonality and slightly finer grain than Tri-X", ["Contrast2012", "GrainAmount", "GrainSize", "curve"]),
             ("very wide latitude", ["Highlights2012", "Shadows2012"]),
             ("produces rich midtones", ["Clarity2012", "curve"])],
        notes="Forgiving all-round B&W.",
        limits=[],
    ),
    dict(
        family="Ilford FP4 Plus", name="Ilford FP4 Plus 125", iso=125, kind="bw", category="Black & white",
        basic=basic(15, -10, 5, 8, -10),
        fx=fx(5, 12, 0),
        curves=curves([(0, 0), (64, 58), (128, 128), (192, 202), (255, 255)]),
        mixer=mixer(Red=5, Orange=8, Yellow=5, Green=-8, Aqua=-5, Blue=-5, Purple=0, Magenta=3),
        grain=grain(18, 18, 40), sharpen=sharpen(60, 0.8, 40, 15), vignette=vignette(0),
        map=[("Fine grain, high sharpness, and smooth gradation", ["GrainAmount", "Sharpness", "Texture", "curve"]),
             ("Favored for landscape and studio work", ["GrayMixerGreen", "GrayMixerBlue"])],
        notes="Landscape and studio; smooth, detailed.",
        limits=[],
    ),
    dict(
        family="Ilford Pan F Plus", name="Ilford Pan F Plus 50", iso=50, kind="bw", category="Black & white",
        basic=basic(30, -5, 0, 12, -18),
        fx=fx(8, 18, 2),
        curves=curves([(0, 0), (64, 50), (128, 128), (192, 210), (255, 255)]),
        mixer=mixer(Red=8, Orange=10, Yellow=8, Green=-12, Aqua=-10, Blue=-10, Purple=-5, Magenta=5),
        grain=grain(6, 10, 25), sharpen=sharpen(70, 0.7, 50, 15), vignette=vignette(0),
        map=[("Pan F is especially fine-grained and contrasty at ISO 50", ["GrainAmount", "Contrast2012", "Blacks2012", "curve"]),
             ("high sharpness", ["Sharpness", "SharpenDetail", "Texture"]),
             ("[extended red sensitivity: reds/oranges render lighter]", ["GrayMixerRed", "GrayMixerOrange"])],
        notes="Bright light only; very crisp. Lower Amount if blacks block up.",
        limits=[],
    ),
    dict(
        family="Kodak T-Max", name="Kodak T-Max 100", iso=100, kind="bw", category="Black & white",
        basic=basic(22, -15, 0, 10, -12),
        fx=fx(6, 15, 0),
        curves=curves([(0, 0), (64, 54), (128, 128), (192, 206), (255, 255)]),
        mixer=mixer(Red=0, Orange=3, Yellow=0, Green=-8, Aqua=-10, Blue=-2, Purple=0, Magenta=2),
        grain=grain(9, 12, 28), sharpen=sharpen(65, 0.8, 45, 15), vignette=vignette(0),
        map=[("T-grain (tabular crystal) technology gives very fine grain and high sharpness", ["GrainAmount", "GrainFrequency", "Sharpness", "Texture"]),
             ("Cleaner, more modern look than Tri-X", ["Clarity2012", "curve"]),
             ("Can be contrasty", ["Contrast2012", "Whites2012"])],
        notes="Clean, modern B&W; architecture and fine detail.",
        limits=[],
    ),
    dict(
        family="Kodak T-Max", name="Kodak T-Max 400", iso=400, kind="bw", category="Black & white",
        basic=basic(25, -15, 0, 12, -15),
        fx=fx(10, 12, 0),
        curves=curves([(0, 0), (64, 52), (128, 128), (192, 208), (255, 255)]),
        mixer=mixer(Red=-2, Orange=2, Yellow=3, Green=-6, Aqua=-8, Blue=2, Purple=2, Magenta=0),
        grain=grain(24, 20, 38), sharpen=sharpen(55, 0.9, 40, 15), vignette=vignette(0),
        map=[("very fine grain and high sharpness", ["GrainAmount", "GrainFrequency", "Sharpness"]),
             ("Can be contrasty and less forgiving if mishandled", ["Contrast2012", "Blacks2012", "curve"]),
             ("[ISO 400: more grain and contrast than T-Max 100, still tighter than Tri-X]", ["GrainAmount", "Contrast2012"])],
        notes="Faster T-grain; cleaner than Tri-X at the same speed.",
        limits=[],
    ),
    dict(
        family="Ilford Delta 3200", name="Ilford Delta 3200", iso=3200, kind="bw", category="Black & white",
        basic=basic(20, -20, 15, 5, -8),
        fx=fx(10, 5, 0),
        curves=curves([(0, 6), (64, 56), (128, 128), (192, 204), (255, 250)]),
        mixer=mixer(Red=5, Orange=8, Yellow=5, Green=-5, Aqua=-5, Blue=5, Purple=0, Magenta=5),
        grain=grain(80, 55, 70), sharpen=sharpen(25, 1.2, 15, 20), vignette=vignette(-12, 45, 60),
        map=[("Very pronounced, stylized grain", ["GrainAmount", "GrainSize", "GrainFrequency"]),
             ("low-light capability", ["Shadows2012", "curve"]),
             ("True speed is closer to ISO 1000-1600", ["[no exposure change: brighten before applying if underexposed]"])],
        notes="Concerts, night, moody low light.",
        limits=[],
    ),
    dict(
        family="Kodak Plus-X", name="Kodak Plus-X 125", iso=125, kind="bw", category="Black & white",
        basic=basic(14, -10, 6, 6, -8),
        fx=fx(4, 8, 0),
        curves=curves([(0, 2), (64, 58), (128, 128), (192, 200), (255, 254)]),
        mixer=mixer(Red=-5, Orange=0, Yellow=3, Green=-3, Aqua=-5, Blue=6, Purple=3, Magenta=0),
        grain=grain(16, 18, 45), sharpen=sharpen(50, 1.0, 30, 10), vignette=vignette(-5, 50, 65),
        map=[("classic medium-speed, balanced look", ["Contrast2012", "curve", "GrayMixerBlue"]),
             ("fine grain", ["GrainAmount", "GrainSize"])],
        notes="Balanced vintage B&W; portraits and everyday.",
        limits=[],
    ),
    dict(
        family="Kodak Panatomic-X", name="Kodak Panatomic-X 32", iso=32, kind="bw", category="Black & white",
        basic=basic(12, -8, 4, 5, -6),
        fx=fx(2, 20, 0),
        curves=curves([(0, 0), (64, 60), (128, 128), (192, 198), (255, 255)]),
        mixer=mixer(Red=-8, Orange=-3, Yellow=0, Green=-5, Aqua=0, Blue=10, Purple=6, Magenta=0),
        grain=grain(3, 8, 25), sharpen=sharpen(75, 0.6, 60, 15), vignette=vignette(0),
        map=[("extraordinarily fine grain", ["GrainAmount", "GrainSize"]),
             ("very high resolving power", ["Sharpness", "SharpenRadius", "SharpenDetail", "Texture"]),
             ("[long, gentle tonal scale]", ["Contrast2012", "curve"])],
        notes="Maximum detail; still life, landscape, architecture.",
        limits=[],
    ),
    dict(
        family="Kodak Double-X", name="Kodak Double-X 5222", iso=250, kind="bw", category="Black & white",
        basic=basic(12, -18, 8, 0, -5),
        fx=fx(5, 5, 0),
        curves=curves([(0, 4), (64, 56), (128, 128), (192, 202), (255, 248)]),
        mixer=mixer(Red=-10, Orange=-5, Yellow=0, Green=-5, Aqua=0, Blue=12, Purple=8, Magenta=2),
        grain=grain(45, 40, 60), sharpen=sharpen(35, 1.1, 20, 10), vignette=vignette(-15, 45, 60),
        map=[("Moderate contrast", ["Contrast2012", "curve"]),
             ("vintage cinematic grain structure", ["GrainAmount", "GrainSize", "GrainFrequency"]),
             ("classic black-and-white cinema", ["Highlights2012", "PostCropVignetteAmount"])],
        notes="Film-noir and cinematic portraits. Box speed 250 (daylight).",
        limits=[],
    ),
    # -------------------------------------------------------- specialty ---
    dict(
        family="Kodak Aerochrome", name="Kodak Aerochrome", iso=None, kind="color", category="Specialty",
        basic=basic(20, -10, 0, 5, -10, sat=15, vib=10),
        fx=fx(5, 5, 3),
        curves=curves([(0, 0), (64, 54), (128, 128), (192, 204), (255, 255)],
                      red=[(0, 0), (64, 72), (128, 142), (255, 255)], green=[(0, 0), (128, 116), (255, 245)]),
        hsl=hsl(Red=(-20, 20, 0), Orange=(-30, 30, 0), Yellow=(-100, 40, -10), Green=(-100, 40, -15),
                Aqua=(10, 10, -5), Blue=(-10, 20, -15), Purple=(0, 10, 0), Magenta=(10, 20, 0)),
        grade=grade(mid=(330, 15, 0), hi=(340, 10, 0), sh=(240, 8, 0)),
        cal=cal(red_hue=-50, red_sat=20, green_hue=-100, green_sat=30, blue_hue=-20, blue_sat=10),
        grain=grain(15, 20, 45), sharpen=sharpen(40, 1.0, 25, 10), vignette=vignette(0),
        map=[("Foliage renders in vivid red, pink, and magenta", ["HueAdjustmentGreen", "HueAdjustmentYellow", "GreenHue", "RedHue", "red", "green", "ColorGradeMidtoneHue", "ColorGradeMidtoneSat"]),
             ("Surreal, otherworldly palette", ["Saturation", "SaturationAdjustmentGreen", "SaturationAdjustmentYellow", "SplitToningHighlightHue"]),
             ("[skies kept deep blue]", ["SaturationAdjustmentBlue", "LuminanceAdjustmentBlue", "SplitToningShadowHue"])],
        notes="Use on scenes with lots of foliage in sun. Results vary strongly by image; reduce Amount if non-foliage areas go too pink.",
        limits=["Real Aerochrome records near-infrared reflectance; a visible-light file has no IR channel, so foliage is recoloured by hue, not by IR. Green objects that aren't plants also turn red/magenta, and foliage reaches orange-red/magenta rather than pure crimson."],
        weak=True,
    ),
    dict(
        family="Kodak High-Speed Infrared", name="Kodak High-Speed Infrared HIE", iso=None, kind="bw", category="Specialty",
        basic=basic(25, -5, 0, 20, -15),
        fx=fx(-20, -10, -15),
        curves=curves([(0, 6), (64, 56), (128, 132), (192, 214), (255, 255)]),
        mixer=mixer(Red=10, Orange=20, Yellow=60, Green=80, Aqua=-60, Blue=-80, Purple=-40, Magenta=0),
        grain=grain(85, 60, 75), sharpen=sharpen(20, 1.2, 15, 20), vignette=vignette(-18, 40, 60),
        map=[("white \"glowing\" foliage", ["GrayMixerGreen", "GrayMixerYellow", "Whites2012"]),
             ("dark skies", ["GrayMixerBlue", "GrayMixerAqua", "GrayMixerPurple"]),
             ("dreamy halation effect", ["Dehaze", "Clarity2012", "Texture"]),
             ("Extremely heavy grain", ["GrainAmount", "GrainSize", "GrainFrequency"])],
        notes="Sunny landscapes with foliage and blue sky.",
        limits=["No real IR data: foliage brightens by colour, not IR reflectance, so green non-plant objects also glow and dark foliage in shade stays darker than on HIE.",
                "HIE's halation (no anti-halation backing) is a spatial glow; approximated with negative Dehaze/Clarity only."],
        weak=True,
    ),
    dict(
        family="Lomochrome Purple", name="Lomochrome Purple", iso=None, kind="color", category="Specialty",
        basic=basic(15, -10, 5, 0, -8, sat=10, vib=5),
        fx=fx(0, 0, 0),
        curves=curves([(0, 4), (64, 58), (128, 128), (192, 202), (255, 252)],
                      red=[(0, 0), (128, 134), (255, 255)], green=[(0, 0), (128, 118), (255, 248)]),
        hsl=hsl(Red=(0, 5, 0), Orange=(-10, 0, 0), Yellow=(-60, 10, 0), Green=(100, 30, -15),
                Aqua=(100, 20, -10), Blue=(-100, 10, 0), Purple=(10, 30, 0), Magenta=(0, 20, 0)),
        grade=grade(sh=(280, 12, 0), mid=(290, 15, 0), hi=(320, 6, 0)),
        cal=cal(green_hue=100, green_sat=20, blue_hue=50, blue_sat=20),
        grain=grain(25, 25, 50), sharpen=sharpen(35, 1.0, 25, 10), vignette=vignette(-8, 50, 60),
        map=[("Shifts greens to purple and magenta", ["HueAdjustmentGreen", "HueAdjustmentAqua", "GreenHue", "green", "ColorGradeMidtoneHue", "ColorGradeMidtoneSat"]),
             ("blues to different hues", ["HueAdjustmentBlue", "BlueHue"]),
             ("variable, unpredictable results", ["[result depends heavily on scene colour; adjust Amount]"])],
        notes="Foliage-heavy scenes. Highly image-dependent; dial Amount to taste.",
        limits=["HSL can move a hue band only ~30 degrees, so greens are pushed through cyan/blue with Calibration and grading rather than truly remapped to purple. Expect blue-violet foliage rather than Lomochrome's full purple."],
        weak=True,
    ),
    dict(
        family="Polaroid", name="Polaroid", iso=None, kind="color", category="Specialty",
        basic=basic(-20, -30, 20, -15, 20, sat=-12, vib=-5),
        fx=fx(-20, -15, -10),
        curves=curves([(0, 28), (64, 78), (128, 132), (192, 190), (255, 236)],
                      red=[(0, 6), (255, 250)], green=[(0, 0), (128, 130), (255, 255)],
                      blue=[(0, 14), (128, 130), (255, 236)]),
        hsl=hsl(Red=(5, -10, 0), Orange=(0, -5, 5), Yellow=(-5, -10, 5), Green=(15, -20, 0),
                Aqua=(-10, -15, 0), Blue=(-10, -20, 10), Purple=(0, -20, 0), Magenta=(0, -15, 0)),
        grade=grade(sh=(185, 10, 0), hi=(50, 12, 0)),
        cal=cal(shadow_tint=-5, red_hue=5),
        grain=grain(30, 40, 70), sharpen=sharpen(10, 1.5, 10, 30), vignette=vignette(-20, 35, 60),
        map=[("soft focus", ["Clarity2012", "Texture", "Dehaze", "Sharpness"]),
             ("lower contrast", ["Contrast2012", "Blacks2012", "Whites2012", "curve"]),
             ("color shifts", ["red", "blue", "SplitToningShadowHue", "SplitToningHighlightHue", "HueAdjustmentGreen"]),
             ("visible chemical texture", ["GrainAmount", "GrainSize", "GrainFrequency"])],
        notes="Casual, nostalgic portraits and still life.",
        limits=["Chemical texture/emulsion marks are spatial artefacts; only Lightroom Grain is used.",
                "The physical white frame cannot be added by a preset (no borders in Lightroom)."],
        weak=True,
    ),
    dict(
        family="Fujifilm Instax", name="Fujifilm Instax", iso=None, kind="color", category="Specialty",
        basic=basic(15, -20, 0, -5, 8, sat=6, vib=10),
        fx=fx(5, 5, 0),
        curves=curves([(0, 14), (64, 62), (128, 130), (192, 204), (255, 246)],
                      blue=[(0, 2), (128, 131), (255, 253)]),
        hsl=hsl(Red=(0, 10, 0), Orange=(-2, 0, 8), Yellow=(0, 5, 0), Green=(10, 5, 0),
                Aqua=(-5, 15, 0), Blue=(0, 10, -5), Purple=(0, 5, 0), Magenta=(0, 8, 0)),
        grade=grade(sh=(210, 6, 0), hi=(200, 4, 0)),
        cal=cal(blue_sat=6),
        grain=grain(18, 25, 50), sharpen=sharpen(45, 1.0, 30, 15), vignette=vignette(-12, 45, 60),
        map=[("crisper, higher contrast", ["Contrast2012", "Clarity2012", "Sharpness"]),
             ("more modern color", ["Saturation", "Vibrance", "SaturationAdjustmentAqua", "LuminanceAdjustmentOrange"]),
             ("framed look", ["PostCropVignetteAmount", "[frame itself not possible]"])],
        notes="Party and lifestyle snaps; brighter skin.",
        limits=["The physical Instax frame cannot be added by a preset."],
    ),
]

# --------------------------------------------------------------------------
# Valid ranges and value types for every key we emit.
# --------------------------------------------------------------------------
RANGES = {
    "Exposure2012": (-0.3, 0.3, float),
    "Contrast2012": (-100, 100, int), "Highlights2012": (-100, 100, int), "Shadows2012": (-100, 100, int),
    "Whites2012": (-100, 100, int), "Blacks2012": (-100, 100, int),
    "Saturation": (-100, 100, int), "Vibrance": (-100, 100, int),
    "Clarity2012": (-100, 100, int), "Texture": (-100, 100, int), "Dehaze": (-100, 100, int),
    "ShadowTint": (-100, 100, int), "RedHue": (-100, 100, int), "RedSaturation": (-100, 100, int),
    "GreenHue": (-100, 100, int), "GreenSaturation": (-100, 100, int),
    "BlueHue": (-100, 100, int), "BlueSaturation": (-100, 100, int),
    "SplitToningShadowHue": (0, 359, int), "SplitToningShadowSaturation": (0, 100, int),
    "SplitToningHighlightHue": (0, 359, int), "SplitToningHighlightSaturation": (0, 100, int),
    "SplitToningBalance": (-100, 100, int),
    "ColorGradeMidtoneHue": (0, 359, int), "ColorGradeMidtoneSat": (0, 100, int),
    "ColorGradeGlobalHue": (0, 359, int), "ColorGradeGlobalSat": (0, 100, int),
    "ColorGradeShadowLum": (-100, 100, int), "ColorGradeMidtoneLum": (-100, 100, int),
    "ColorGradeHighlightLum": (-100, 100, int), "ColorGradeGlobalLum": (-100, 100, int),
    "ColorGradeBlending": (0, 100, int),
    "GrainAmount": (0, 100, int), "GrainSize": (0, 100, int), "GrainFrequency": (0, 100, int),
    "Sharpness": (0, 150, int), "SharpenRadius": (0.5, 3.0, float),
    "SharpenDetail": (0, 100, int), "SharpenEdgeMasking": (0, 100, int),
    "PostCropVignetteAmount": (-100, 100, int), "PostCropVignetteMidpoint": (0, 100, int),
    "PostCropVignetteFeather": (0, 100, int), "PostCropVignetteRoundness": (-100, 100, int),
    "PostCropVignetteStyle": (1, 3, int), "PostCropVignetteHighlightContrast": (0, 100, int),
}
for _c in HSL_CHANNELS:
    for _p in ("HueAdjustment", "SaturationAdjustment", "LuminanceAdjustment", "GrayMixer"):
        RANGES[f"{_p}{_c}"] = (-100, 100, int)

CURVE_KEYS = {"master": "ToneCurvePV2012", "red": "ToneCurvePV2012Red",
              "green": "ToneCurvePV2012Green", "blue": "ToneCurvePV2012Blue"}

# --------------------------------------------------------------------------
# Flatten a stock into crs attributes + curve sequences.
# --------------------------------------------------------------------------


def settings(stock):
    s = {}
    for part in ("basic", "fx", "grain", "sharpen", "vignette"):
        s.update(stock[part])
    if stock["kind"] == "bw":
        s.update(stock["mixer"])
    else:
        s.update(stock["hsl"])
        s.update(stock["grade"])
        s.update(stock["cal"])
    return s


def fmt(key, v):
    if key == "Exposure2012":
        return f"{v:+.2f}"
    if key == "SharpenRadius":
        return f"{v:+.1f}"
    return f"{v:+d}" if RANGES[key][0] < 0 and v > 0 else str(v)


def safe_filename(name):
    return re.sub(r'[\\/:*?"<>|]', "-", name).strip(". ")


def alt(tag, text):
    return (f"   <crs:{tag}>\n    <rdf:Alt>\n"
            f'     <rdf:li xml:lang="x-default">{escape(text)}</rdf:li>\n'
            f"    </rdf:Alt>\n   </crs:{tag}>")


def seq(tag, pts):
    items = "\n".join(f"     <rdf:li>{x}, {y}</rdf:li>" for x, y in pts)
    return f"   <crs:{tag}>\n    <rdf:Seq>\n{items}\n    </rdf:Seq>\n   </crs:{tag}>"


def description(stock):
    iso = f"ISO {stock['iso']}. " if stock["iso"] else ""
    return (f"{stock['family']} - {stock['category']} film approximation. {iso}{stock['notes']} "
            "Visual approximation built from Lightroom sliders; not an exact reproduction.")


def xmp(stock, preset_uuid, sort_index):
    bw = stock["kind"] == "bw"
    s = settings(stock)
    attrs = [
        ("PresetType", "Normal"), ("Cluster", ""), ("UUID", preset_uuid),
        ("SupportsAmount", "True"),
        ("SupportsColor", "True"),
        ("SupportsMonochrome", "True" if bw else "False"),
        ("SupportsHighDynamicRange", "True"), ("SupportsNormalDynamicRange", "True"),
        ("SupportsSceneReferred", "True"), ("SupportsOutputReferred", "True"),
        ("CameraModelRestriction", ""), ("Copyright", ""), ("ContactInfo", ""),
        ("Version", CRS_VERSION), ("ProcessVersion", PROCESS_VERSION),
    ]
    attrs += [(k, fmt(k, v)) for k, v in s.items()]
    attrs += [("ConvertToGrayscale", "True" if bw else "False"),
              ("ToneCurveName2012", "Custom"), ("HasSettings", "True")]
    attr_xml = "\n".join(f'   crs:{k}="{escape(str(v))}"' for k, v in attrs)
    curve_xml = "\n".join(seq(CURVE_KEYS[c], stock["curves"][c]) for c in ("master", "red", "green", "blue"))
    return f"""<x:xmpmeta xmlns:x="{NS_X}" x:xmptk="Adobe XMP Core 7.0-c000 1.000000, 0000/00/00-00:00:00        ">
 <rdf:RDF xmlns:rdf="{NS_RDF}">
  <rdf:Description rdf:about=""
    xmlns:crs="{NS_CRS}"
{attr_xml}>
{alt("Name", stock["name"])}
{alt("ShortName", stock["name"])}
{alt("SortName", f"{sort_index:02d} {stock['name']}")}
{alt("Group", GROUP)}
{alt("Description", description(stock))}
{curve_xml}
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
"""

# --------------------------------------------------------------------------
# Source text (RTF) -> plain text, for verbatim trait checks.
# --------------------------------------------------------------------------


def source_text():
    s = SOURCE.read_text(encoding="utf-8")
    s = re.sub(r"\\'([0-9a-fA-F]{2})", lambda m: bytes.fromhex(m.group(1)).decode("cp1252"), s)
    s = re.sub(r"\\u(-?\d+) ?", lambda m: chr(int(m.group(1)) % 65536), s)
    s = s.replace("\\\n", "\n")
    s = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", s)
    s = s.replace("\\{", "").replace("\\}", "").replace("{", "").replace("}", "")
    s = s[s.index("Different Film types list:"):]
    return re.sub(r"\s+", " ", s)

# --------------------------------------------------------------------------
# README rendering.
# --------------------------------------------------------------------------


def label(key):
    if key in CURVE_KEYS:
        return f"{key.capitalize() if key != 'master' else 'Point'} curve"
    for prefix, short in (("HueAdjustment", "HSL Hue"), ("SaturationAdjustment", "HSL Sat"),
                          ("LuminanceAdjustment", "HSL Lum"), ("GrayMixer", "B&W Mix")):
        if key.startswith(prefix):
            return f"{short} {key[len(prefix):]}"
    return {"Contrast2012": "Contrast", "Highlights2012": "Highlights", "Shadows2012": "Shadows",
            "Whites2012": "Whites", "Blacks2012": "Blacks", "Clarity2012": "Clarity",
            "Exposure2012": "Exposure", "GrainFrequency": "Grain Roughness",
            "SplitToningShadowHue": "Grade Shadow Hue", "SplitToningShadowSaturation": "Grade Shadow Sat",
            "SplitToningHighlightHue": "Grade Highlight Hue", "SplitToningHighlightSaturation": "Grade Highlight Sat",
            "ColorGradeMidtoneHue": "Grade Midtone Hue", "ColorGradeMidtoneSat": "Grade Midtone Sat",
            "ColorGradeGlobalHue": "Grade Global Hue", "ColorGradeGlobalSat": "Grade Global Sat",
            "RedHue": "Calib Red Hue", "RedSaturation": "Calib Red Sat", "GreenHue": "Calib Green Hue",
            "GreenSaturation": "Calib Green Sat", "BlueHue": "Calib Blue Hue", "BlueSaturation": "Calib Blue Sat",
            "ShadowTint": "Calib Shadow Tint", "PostCropVignetteAmount": "Vignette",
            "SharpenRadius": "Sharpen Radius", "SharpenDetail": "Sharpen Detail"}.get(key, key)


def render_keys(stock, keys):
    s = settings(stock)
    out = []
    for k in keys:
        if k.startswith("["):
            out.append(k.strip("[]"))
        elif k == "curve":
            out.append("Point curve " + " ".join(f"{x}→{y}" for x, y in stock["curves"]["master"]))
        elif k in CURVE_KEYS:
            out.append(f"{label(k)} " + " ".join(f"{x}→{y}" for x, y in stock["curves"][k]))
        else:
            out.append(f"{label(k)} {fmt(k, s[k])}")
    return "; ".join(out)


def readme(stocks):
    families = []
    for st in stocks:
        if st["family"] not in families:
            families.append(st["family"])
    lines = [
        "# Iconic Film Stocks for Lightroom",
        "",
        f"{len(stocks)} presets in {len(families)} families for **Lightroom** (the cloud-based desktop app, formerly "
        "\"Lightroom CC\"), **not** Lightroom Classic. Every preset is a *visual approximation* of a film stock, "
        "built only from standard Lightroom sliders: no camera profiles, LUTs, white balance or local adjustments. "
        "That keeps them portable across cameras and images.",
        "",
        "## Import (Lightroom desktop)",
        "",
        "1. Open a photo in **Edit**, then open the **Presets** panel.",
        "2. Click **⋯** (top of the Presets panel) → **Import Presets…**.",
        f"3. Select **`{COLLECTION}.zip`**. You don't need to unzip it. You can also select individual `.xmp` files.",
        f"4. Confirm all {len(stocks)} presets appear together under **Yours → {GROUP}**.",
        "",
        "Imported presets **sync through Adobe's cloud** to Lightroom on your other computers, iPhone/iPad, Android and the web.",
        "",
        f"**One group:** every preset's `crs:Group` is **{GROUP}**, and the zip holds a single `{COLLECTION}/` "
        "folder with all the `.xmp` files directly inside it (no subfolders), so the whole set imports into one "
        "group. Presets within it list alphabetically, which keeps each brand's stocks next to each other; the film "
        "family is noted in each preset's description. If your Lightroom version ever files them elsewhere, select "
        f"them, right-click → **Move**, and choose **{GROUP}**.",
        "",
        "**Amount:** every preset supports Lightroom's preset **Amount** slider (0-200). Lower it to tone a look down.",
        "",
        "## Schema / version values",
        "",
        "No Lightroom-exported sample preset was supplied, so the files follow the current Camera Raw settings "
        f"schema (`{NS_CRS}`): `crs:Version=\"{CRS_VERSION}\"` and `crs:ProcessVersion=\"{PROCESS_VERSION}\"` "
        "(Process Version 6, introduced with Camera Raw 15.4 in June 2023). Applying a preset therefore sets the "
        "photo to PV6, the current default for new photos. Color Grading uses the `ColorGrade*` keys, plus the "
        "`SplitToning*` keys that Color Grading reuses for shadow/highlight hue, saturation and balance.",
        "",
        "## Presets",
        "",
        "| Family | Preset | ISO | Type | Contrast | Saturation | Grain | Usage |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for st in stocks:
        s = settings(st)
        lines.append(f"| {st['family']} | {st['name']} | {st['iso'] or '—'} | {st['category']} | "
                     f"{fmt('Contrast2012', s['Contrast2012'])} | "
                     f"{'B&W' if st['kind'] == 'bw' else fmt('Saturation', s['Saturation'])} | "
                     f"{s['GrainAmount']}/{s['GrainSize']}/{s['GrainFrequency']} | {st['notes']} |")
    lines += ["", "Grain is shown as Amount/Size/Roughness.", "",
              "## Trait → setting mapping", "",
              "Quoted traits come verbatim from `film_stocks.txt`. Bracketed rows are derived notes, such as how "
              "ISO variants within a family are told apart. Values are the actual preset values.", ""]
    for st in stocks:
        lines += [f"### {st['name']}", "", "| Trait | Settings |", "|---|---|"]
        for trait, keys in st["map"]:
            t = trait.strip("[]") if trait.startswith("[") else f"“{trait}”"
            lines.append(f"| {t.replace('|', '/')} | {render_keys(st, keys).replace('|', '/')} |")
        lines.append("")
    lines += ["## Approximation limits", "",
              "These presets are approximations. Lightroom presets can't reproduce spatial effects (glow, halation, "
              "borders, emulsion damage), infrared data, or the exact dye chemistry of a process. Specifically:", ""]
    lines.append("- **All stocks:** real film response depends on exposure, development and scanning. A preset "
                 "re-maps tones and colours of a digital file and can't add dynamic range that wasn't captured.")
    for st in stocks:
        for lim in st["limits"]:
            lines.append(f"- **{st['name']}:** {lim}")
    lines += ["", "**Flagged as weak approximations:** "
              + ", ".join(st["name"] for st in stocks if st.get("weak")) + ".", "",
              "## Usage notes", ""]
    for st in stocks:
        lines.append(f"- **{st['name']}:** {st['notes']}")
    lines += ["", "## Rebuilding", "", "```sh", "python3 build_presets.py", "```", "",
              "Each build creates fresh random UUIDs (uuid4). If you re-import a rebuilt set, delete the old "
              "groups in Lightroom first to avoid duplicates.", ""]
    return "\n".join(lines)

# --------------------------------------------------------------------------
# Build + validate.
# --------------------------------------------------------------------------

REQUIRED = {
    "Kodachrome": ["Kodachrome 25", "Kodachrome 64", "Kodachrome 200"],
    "Fujifilm Velvia": ["Fujifilm Velvia 50", "Fujifilm Velvia 100"],
    "Fujifilm Provia": ["Fujifilm Provia 100F"],
    "Kodak Ektachrome": ["Kodak Ektachrome E100"],
    "Kodak Portra": ["Kodak Portra 160", "Kodak Portra 400", "Kodak Portra 800"],
    "Kodak Ektar": ["Kodak Ektar 100"],
    "Kodak Gold": ["Kodak Gold 200"],
    "Fujifilm Pro 400H": ["Fujifilm Pro 400H"],
    "Fujifilm Superia": ["Fujifilm Superia 400"],
    "CineStill": ["CineStill 800T"],
    "Kodak Vision3": ["Kodak Vision3 500T"],
    "Kodak Tri-X": ["Kodak Tri-X 400"],
    "Ilford HP5 Plus": ["Ilford HP5 Plus 400"],
    "Ilford FP4 Plus": ["Ilford FP4 Plus 125"],
    "Ilford Pan F Plus": ["Ilford Pan F Plus 50"],
    "Kodak T-Max": ["Kodak T-Max 100", "Kodak T-Max 400"],
    "Ilford Delta 3200": ["Ilford Delta 3200"],
    "Kodak Plus-X": ["Kodak Plus-X 125"],
    "Kodak Panatomic-X": ["Kodak Panatomic-X 32"],
    "Kodak Double-X": ["Kodak Double-X 5222"],
    "Kodak Aerochrome": ["Kodak Aerochrome"],
    "Kodak High-Speed Infrared": ["Kodak High-Speed Infrared HIE"],
    "Lomochrome Purple": ["Lomochrome Purple"],
    "Polaroid": ["Polaroid"],
    "Fujifilm Instax": ["Fujifilm Instax"],
}
FORBIDDEN_LABEL_WORDS = ("Style", "Look", "Inspired", "Vibe")


def validate_definitions(stocks, src):
    errors = []
    for st in stocks:
        s = settings(st)
        for k, v in s.items():
            lo, hi, typ = RANGES[k]
            if type(v) is not typ:
                errors.append(f"{st['name']}: {k} type {type(v).__name__}, expected {typ.__name__}")
            elif not lo <= v <= hi:
                errors.append(f"{st['name']}: {k}={v} outside {lo}..{hi}")
        for c, pts in st["curves"].items():
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            if xs[0] != 0 or xs[-1] != 255 or any(b <= a for a, b in zip(xs, xs[1:])):
                errors.append(f"{st['name']}: {c} curve x points invalid {pts}")
            if any(not 0 <= y <= 255 for y in ys) or any(b < a for a, b in zip(ys, ys[1:])):
                errors.append(f"{st['name']}: {c} curve not monotonic/in range {pts}")
        for trait, keys in st["map"]:
            if not trait.startswith("[") and trait not in src:
                errors.append(f"{st['name']}: trait not found verbatim in film_stocks.txt: {trait!r}")
            for k in keys:
                if not (k.startswith("[") or k == "curve" or k in CURVE_KEYS or k in s):
                    errors.append(f"{st['name']}: mapped key {k} not set by preset")
        if any(w in st["name"].split() for w in FORBIDDEN_LABEL_WORDS):
            errors.append(f"{st['name']}: forbidden suffix word in label")
    # No two presets may be identical apart from the name.
    seen = {}
    for st in stocks:
        fp = (tuple(sorted(settings(st).items())), tuple((c, tuple(p)) for c, p in sorted(st["curves"].items())))
        if fp in seen:
            errors.append(f"{st['name']} has identical settings to {seen[fp]}")
        seen[fp] = st["name"]
    return errors


def validate_output(stocks):
    errors, rows, uuids = [], [], []
    ns = {"x": NS_X, "rdf": NS_RDF, "crs": NS_CRS}
    files = sorted(TREE.glob("*.xmp"))
    subdirs = [d.name for d in TREE.iterdir() if d.is_dir()]
    if subdirs:
        errors.append(f"output folder must be flat, found subfolders {subdirs}")
    with zipfile.ZipFile(ZIP_PATH) as zf:
        bad = [n for n in zf.namelist() if not re.fullmatch(re.escape(COLLECTION) + r"/[^/]+\.xmp", n)]
    if bad:
        errors.append(f"zip entries outside the single '{COLLECTION}/' folder: {bad}")
    by_name = {st["name"]: st for st in stocks}
    found = {}
    for f in files:
        try:
            root = ET.parse(f).getroot()
        except ET.ParseError as e:
            errors.append(f"{f}: XML parse error {e}")
            continue
        d = root.find("rdf:RDF/rdf:Description", ns)
        a = {k.split("}")[1]: v for k, v in d.attrib.items() if k.startswith("{" + NS_CRS)}

        def alt_text(tag):
            el = d.find(f"crs:{tag}/rdf:Alt/rdf:li", ns)
            return el.text if el is not None else None

        name, short, group = alt_text("Name"), alt_text("ShortName"), alt_text("Group")
        folder, stem = f.parent.name, f.stem
        if not name:
            errors.append(f"{f}: empty name")
        if not (folder == group == GROUP):
            errors.append(f"{f}: folder {folder!r} / group {group!r} must both be {GROUP!r}")
        if not (stem == safe_filename(name) and name == short):
            errors.append(f"{f}: filename/Name/ShortName mismatch {stem!r} {name!r} {short!r}")
        st = by_name.get(name)
        if st is None:
            errors.append(f"{f}: unexpected preset {name!r}")
            continue
        found.setdefault(st["family"], []).append(name)
        uuids.append(a.get("UUID"))
        if not re.fullmatch(r"[0-9A-F]{32}", a.get("UUID", "")):
            errors.append(f"{f}: UUID not uppercase 32-hex")
        if a.get("SupportsAmount") != "True":
            errors.append(f"{f}: SupportsAmount != True")
        bw = st["kind"] == "bw"
        if a.get("ConvertToGrayscale") != ("True" if bw else "False"):
            errors.append(f"{f}: ConvertToGrayscale wrong for {'B&W' if bw else 'colour'} preset")
        if bw and a.get("SupportsMonochrome") != "True":
            errors.append(f"{f}: B&W preset must support monochrome")
        if a.get("Copyright") != "" or a.get("ContactInfo") != "":
            errors.append(f"{f}: Copyright/ContactInfo must be empty")
        for banned in ("Temperature", "Tint", "CameraProfile", "LensProfileEnable", "CropTop"):
            if banned in a:
                errors.append(f"{f}: forbidden key {banned}")
        for k, v in a.items():
            if k in RANGES:
                lo, hi, typ = RANGES[k]
                try:
                    num = typ(float(v)) if typ is float else int(v)
                except ValueError:
                    errors.append(f"{f}: {k}={v!r} not {typ.__name__}")
                    continue
                if not lo <= num <= hi:
                    errors.append(f"{f}: {k}={v} out of range")
        rows.append((st["family"], name, group, f.name, st["iso"] or "—",
                     a["Contrast2012"], "B&W" if bw else a["Saturation"], a["GrainAmount"]))
    if len(set(uuids)) != len(uuids):
        errors.append("duplicate UUIDs")
    for fam, names in REQUIRED.items():
        for n in names:
            if n not in found.get(fam, []):
                errors.append(f"missing required preset {fam} / {n}")
    extra = {n for ns_ in found.values() for n in ns_} - {n for ns_ in REQUIRED.values() for n in ns_}
    if extra:
        errors.append(f"unexpected presets {sorted(extra)}")
    return errors, rows


def build():
    src = source_text()
    errs = validate_definitions(STOCKS, src)
    if errs:
        sys.exit("Definition errors:\n  " + "\n  ".join(errs))

    if TREE.exists():
        shutil.rmtree(TREE)  # also removes the old per-family subfolders
    TREE.mkdir(parents=True)
    for i, st in enumerate(STOCKS, 1):
        (TREE / f"{safe_filename(st['name'])}.xmp").write_text(
            xmp(st, uuid.uuid4().hex.upper(), i), encoding="utf-8")

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(TREE.glob("*.xmp")):
            zf.write(f, arcname=f.relative_to(OUT).as_posix())
    (OUT / "README.md").write_text(readme(STOCKS), encoding="utf-8")

    errs, rows = validate_output(STOCKS)
    hdr = ("Family", "Preset", "Group", "File", "ISO", "Contrast", "Sat", "Grain")
    widths = [max(len(str(r[i])) for r in rows + [hdr]) for i in range(len(hdr))]
    line = lambda r: "  ".join(str(c).ljust(w) for c, w in zip(r, widths))
    print(line(hdr))
    print(line(["-" * w for w in widths]))
    for r in rows:
        print(line(r))
    with zipfile.ZipFile(ZIP_PATH) as zf:
        zipped = len([n for n in zf.namelist() if n.endswith(".xmp")])
    print(f"\n{len(rows)} presets, {len({r[0] for r in rows})} families, {zipped} files in {ZIP_PATH.name}")
    if errs:
        sys.exit("VALIDATION FAILED:\n  " + "\n  ".join(errs))
    print(f"VALIDATION PASSED: XML well-formed; single flat folder + zip folder; folder == Group == '{GROUP}' "
          "for every preset; filename == Name == ShortName; "
          "UUIDs unique; all required presets present; values in range; grayscale flags correct; "
          "all quoted traits found verbatim in film_stocks.txt; no duplicate settings.")


if __name__ == "__main__":
    build()
