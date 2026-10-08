#!/usr/bin/env python3
"""Generate Lightroom XMP presets that only set the master (RGB / luminance)
point curve: a grid of contrast levels x black-fade levels x highlight
roll-off levels.

Each preset writes ONLY:
    crs:ToneCurvePV2012      (master point curve)
    crs:ToneCurveName2012    (curve label shown in the UI)

The Red/Green/Blue channel curves, the parametric curve sliders, exposure,
colour and everything else are left untouched, so these stack cleanly on top
of the Concert LED Skin Fix presets.

Run:  python3 tools/generate_contrast_presets.py
Output:
    presets/Concert Contrast + Fade/*.xmp                 (full whites)
    presets/Concert Contrast + Fade - H<n> .../*.xmp     (rolled-off whites)
    dist/Concert-Contrast-Fade-Presets.zip   (import this into Lightroom)
"""

import math
import uuid
import zipfile

from generate_presets import ROOT, UUID_NS, alt, seq

GROUP = "Concert Contrast + Fade"
ZIP_PATH = ROOT / "dist" / "Concert-Contrast-Fade-Presets.zip"

# Seven control points: extra points at 32 and 224 give the toe and shoulder
# enough shape for a matte fade without the spline overshooting.
XS = (0, 32, 64, 128, 192, 224, 255)

# (label, S-curve amplitude). Amplitude is the max shift, in 0-255 levels, of
# the S-curve at roughly the quarter tones (darken shadows / brighten lights).
# The midpoint (128) and white point (255) never move.
CONTRAST = (
    ("C0 Flat", 0),
    ("C1 Soft", 8),
    ("C2 Medium", 14),
    ("C3 Strong", 20),
    ("C4 Punchy", 28),
)

# (label, black lift). Output level that pure black is raised to.
FADE = (
    ("F0 No Fade", 0),
    ("F1 Light Fade", 12),
    ("F2 Medium Fade", 24),
    ("F3 Heavy Fade", 40),
)

# (label, white drop). How many levels pure white is pulled down (255 - drop),
# for a softer, filmic shoulder. H0 presets live in the base GROUP with their
# original names; each other level gets its own group.
HIGHLIGHTS = (
    ("H0 Full Whites", 0),
    ("H1 Soft Highlights", 10),
    ("H2 Medium Highlights", 20),
    ("H3 Matte Highlights", 30),
)

# Fade falls off as (1 - y/255)^FADE_FALLOFF: strongest in the blacks, nearly
# gone by the midtones, zero at white. Monotonic as long as
# FADE_FALLOFF * lift < 255.
FADE_FALLOFF = 3

# Highlight roll-off falls off as (y/255)^HIGHLIGHT_FALLOFF: strongest at white,
# nearly gone by the midtones, zero at black. Monotonic as long as
# HIGHLIGHT_FALLOFF * drop < 255.
HIGHLIGHT_FALLOFF = 3


def curve(s, lift, drop=0):
    """Master curve: an S-curve, then a black fade and a highlight roll-off,
    both applied to its output so the result stays monotonic."""
    assert FADE_FALLOFF * lift < 255 and HIGHLIGHT_FALLOFF * drop < 255
    pts = []
    for x in XS:
        t = x / 255.0
        y = x - s * math.sin(2 * math.pi * t)
        y = y + lift * (1 - y / 255.0) ** FADE_FALLOFF
        y = y - drop * (y / 255.0) ** HIGHLIGHT_FALLOFF
        pts.append((x, max(0, min(255, round(y)))))
    ys = [y for _, y in pts]
    assert all(b > a for a, b in zip(ys, ys[1:])), f"non-monotonic curve {pts}"
    return pts


def xmp(name, sort_name, desc, curve_name, pts, group=GROUP):
    preset_uuid = uuid.uuid5(UUID_NS, f"{group}/{name}").hex.upper()
    return f"""<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core 7.0-c000 1.000000, 0000/00/00-00:00:00        ">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:crs="http://ns.adobe.com/camera-raw-settings/1.0/"
   crs:PresetType="Normal"
   crs:Cluster=""
   crs:UUID="{preset_uuid}"
   crs:SupportsAmount="False"
   crs:SupportsColor="True"
   crs:SupportsMonochrome="True"
   crs:SupportsHighDynamicRange="True"
   crs:SupportsNormalDynamicRange="True"
   crs:SupportsSceneReferred="True"
   crs:SupportsOutputReferred="True"
   crs:CameraModelRestriction=""
   crs:Copyright=""
   crs:ContactInfo=""
   crs:Version="15.0"
   crs:ToneCurveName2012="{curve_name}"
   crs:HasSettings="True">
{alt("Name", name)}
{alt("ShortName", name)}
{alt("SortName", sort_name)}
{alt("Group", group)}
{alt("Description", desc)}
{seq("ToneCurvePV2012", pts)}
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
"""


def build():
    presets = []  # (group, filename, body)
    for hi, (h_label, drop) in enumerate(HIGHLIGHTS):
        group = GROUP if drop == 0 else f"{GROUP} - {h_label}"
        for ci, (c_label, s) in enumerate(CONTRAST):
            for fi, (f_label, lift) in enumerate(FADE):
                if s == 0 and lift == 0 and drop == 0:
                    continue  # identical to the reset preset below
                name = f"{c_label} - {f_label}"
                if drop:
                    name += f" - {h_label}"
                desc = (
                    f"Master luminance curve only. Contrast: {c_label[3:]} "
                    f"(S-curve {s}). Blacks: {f_label[3:]} (black lifted to {lift}). "
                    + (f"Highlights: {h_label[3:]} (white at {255 - drop}). " if drop else "")
                    + "Colour channel curves untouched."
                )
                body = xmp(name, f"{ci}{fi}{hi} {name}" if drop else f"{ci}{fi} {name}",
                           desc, "Custom", curve(s, lift, drop), group)
                presets.append((group, f"{name}.xmp", body))

    presets.append((
        GROUP,
        "Reset Luminance Curve.xmp",
        xmp("Reset Luminance Curve", "99 Reset Luminance Curve",
            "Sets the master point curve back to linear. Colour channel curves untouched.",
            "Linear", [(0, 0), (255, 255)]),
    ))

    for group in {g for g, _, _ in presets}:
        out = ROOT / "presets" / group
        out.mkdir(parents=True, exist_ok=True)
        for old in out.glob("*.xmp"):
            old.unlink()
    for group, filename, body in presets:
        (ROOT / "presets" / group / filename).write_text(body, encoding="utf-8")

    ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for group, filename, _ in presets:
            zf.write(ROOT / "presets" / group / filename, arcname=f"{group}/{filename}")

    print(f"Wrote {len(presets)} presets to presets/{GROUP}*")
    print(f"Wrote {ZIP_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
