#!/usr/bin/env python3
"""Generate Lightroom (cloud / "Lightroom CC") XMP presets that only touch the
Red, Green and Blue point curves, for neutralising coloured LED stage light on
skin.

Each preset writes ONLY these settings:
    crs:ToneCurvePV2012Red
    crs:ToneCurvePV2012Green
    crs:ToneCurvePV2012Blue

The master RGB curve, white balance, exposure, HSL, profile and process
version are left untouched, so a preset can be layered over any edit.

Run:  python3 tools/generate_presets.py
Output:
    presets/Concert LED Skin Fix/*.xmp
    dist/Concert-LED-Skin-Fix-Presets.zip   (import this into Lightroom)
"""

import math
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GROUP = "Concert LED Skin Fix"
OUT_DIR = ROOT / "presets" / GROUP
ZIP_PATH = ROOT / "dist" / "Concert-LED-Skin-Fix-Presets.zip"

# Fixed namespace so regenerating keeps the same preset UUIDs (Lightroom then
# treats a re-import as an update rather than a duplicate).
UUID_NS = uuid.UUID("6f1c2a0e-9a51-4c4b-8f4e-3c1d2b7a9e10")

# Input positions of the curve control points. Five points keeps Lightroom's
# spline smooth and leaves the curves easy to hand-tweak afterwards.
XS = (0, 64, 128, 192, 255)

# Global S-curve contrast added to every channel at "Medium". LED washes flatten
# the non-dominant channels; a gentle S restores separation in each one.
S_CONTRAST = 6

# Strength multipliers applied to the midtone shifts, contrast and white-point
# pull of each cast recipe.
STRENGTHS = (
    ("1 Subtle", 0.55),
    ("2 Medium", 1.0),
    ("3 Strong", 1.6),
)

# Cast recipes at "Medium" strength.
#   shift  : midtone move for (R, G, B). Negative pulls the cast colour out,
#            positive puts the missing colour back. Skin should end up with
#            R > G > B, so red is lifted most and blue least when restoring.
#   white  : how far to lower each channel's white point (tames a clipped,
#            fully saturated cast channel in the highlights).
#   s      : per-channel multiplier on S_CONTRAST.
CASTS = (
    {
        "key": "01", "name": "Red Wash",
        "desc": "Red LED light. Pulls red out of the midtones/highlights and "
                "restores green and blue so skin reads warm-neutral instead of crimson.",
        "shift": (-30, 30, 22), "white": (14, 0, 0), "s": (1.0, 1.0, 0.8),
    },
    {
        "key": "02", "name": "Orange-Amber Wash",
        "desc": "Orange / amber / tungsten-style LED. Mostly a blue deficit with "
                "excess red; restores blue and trims red.",
        "shift": (-18, 6, 34), "white": (8, 0, 0), "s": (1.0, 1.0, 0.8),
    },
    {
        "key": "03", "name": "Yellow Wash",
        "desc": "Yellow LED. Red and green both too high, blue crushed. Trims "
                "green more than red and restores blue.",
        "shift": (-6, -20, 36), "white": (0, 8, 0), "s": (1.0, 1.0, 0.8),
    },
    {
        "key": "04", "name": "Green Wash",
        "desc": "Green LED. Pulls green and restores red (plus a little blue) "
                "to remove the sickly cast from skin.",
        "shift": (28, -30, 12), "white": (0, 14, 0), "s": (1.0, 1.0, 0.8),
    },
    {
        "key": "05", "name": "Cyan-Teal Wash",
        "desc": "Cyan / teal LED. Red is the missing channel; restores red and "
                "trims green and blue.",
        "shift": (36, -14, -18), "white": (0, 6, 8), "s": (1.0, 1.0, 0.8),
    },
    {
        "key": "06", "name": "Blue Wash",
        "desc": "Blue LED. Pulls blue hard and restores red (more) and green "
                "(less) to bring skin back toward natural warmth.",
        "shift": (32, 20, -34), "white": (0, 0, 14), "s": (1.0, 1.0, 1.0),
    },
    {
        "key": "07", "name": "Purple-Violet Wash",
        "desc": "Purple / violet / UV-ish LED. Blue-dominant with some red; "
                "pulls blue, restores green, nudges red slightly.",
        "shift": (6, 30, -30), "white": (0, 0, 12), "s": (1.0, 1.0, 1.0),
    },
    {
        "key": "08", "name": "Magenta-Pink Wash",
        "desc": "Magenta / pink LED. Green is the missing channel; restores "
                "green and trims red and blue.",
        "shift": (-14, 30, -20), "white": (6, 0, 8), "s": (1.0, 1.0, 1.0),
    },
)


def curve(shift, white, s):
    """Return [(x, y), ...] for one channel.

    y = x + shift * bump(x) + s * scurve(x) - white * (x/255)^2
      bump(x)   = sin(pi * x/255)      -> 0 at the ends, 1 at the midpoint
      scurve(x) = -sin(2 * pi * x/255) -> darkens shadows, brightens highlights
    The black point is always pinned at 0 so shadows stay true black.
    """
    pts = []
    for x in XS:
        t = x / 255.0
        y = x + shift * math.sin(math.pi * t) - s * math.sin(2 * math.pi * t) - white * t * t
        pts.append((x, max(0, min(255, round(y)))))
    ys = [y for _, y in pts]
    assert all(b > a for a, b in zip(ys, ys[1:])), f"non-monotonic curve {pts}"
    return pts


def seq(tag, pts):
    items = "\n".join(f"     <rdf:li>{x}, {y}</rdf:li>" for x, y in pts)
    return (
        f"   <crs:{tag}>\n"
        f"    <rdf:Seq>\n{items}\n"
        f"    </rdf:Seq>\n"
        f"   </crs:{tag}>"
    )


def alt(tag, text):
    return (
        f"   <crs:{tag}>\n"
        f"    <rdf:Alt>\n"
        f'     <rdf:li xml:lang="x-default">{text}</rdf:li>\n'
        f"    </rdf:Alt>\n"
        f"   </crs:{tag}>"
    )


def xmp(name, sort_name, desc, curves):
    preset_uuid = uuid.uuid5(UUID_NS, name).hex.upper()
    r, g, b = curves
    return f"""<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core 7.0-c000 1.000000, 0000/00/00-00:00:00        ">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:crs="http://ns.adobe.com/camera-raw-settings/1.0/"
   crs:PresetType="Normal"
   crs:Cluster=""
   crs:UUID="{preset_uuid}"
   crs:SupportsAmount="False"
   crs:SupportsColor="True"
   crs:SupportsMonochrome="False"
   crs:SupportsHighDynamicRange="True"
   crs:SupportsNormalDynamicRange="True"
   crs:SupportsSceneReferred="True"
   crs:SupportsOutputReferred="True"
   crs:CameraModelRestriction=""
   crs:Copyright=""
   crs:ContactInfo=""
   crs:Version="15.0"
   crs:HasSettings="True">
{alt("Name", name)}
{alt("ShortName", name)}
{alt("SortName", sort_name)}
{alt("Group", GROUP)}
{alt("Description", desc)}
{seq("ToneCurvePV2012Red", r)}
{seq("ToneCurvePV2012Green", g)}
{seq("ToneCurvePV2012Blue", b)}
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
"""


def build():
    presets = []
    for cast in CASTS:
        for label, k in STRENGTHS:
            curves = [
                curve(cast["shift"][i] * k, cast["white"][i] * k, S_CONTRAST * cast["s"][i] * k)
                for i in range(3)
            ]
            name = f"{cast['name']} - {label}"
            sort = f"{cast['key']} {name}"
            presets.append((f"{cast['key']} {name}.xmp", xmp(name, sort, cast["desc"], curves)))

    linear = [(0, 0), (255, 255)]
    presets.append((
        "99 Reset RGB Channel Curves.xmp",
        xmp("Reset RGB Channel Curves", "99 Reset RGB Channel Curves",
            "Sets the Red, Green and Blue point curves back to linear. "
            "Does not touch the master RGB curve.",
            [linear, linear, linear]),
    ))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.xmp"):
        old.unlink()
    for filename, body in presets:
        (OUT_DIR / filename).write_text(body, encoding="utf-8")

    ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, _ in presets:
            zf.write(OUT_DIR / filename, arcname=f"{GROUP}/{filename}")

    print(f"Wrote {len(presets)} presets to {OUT_DIR.relative_to(ROOT)}")
    print(f"Wrote {ZIP_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
