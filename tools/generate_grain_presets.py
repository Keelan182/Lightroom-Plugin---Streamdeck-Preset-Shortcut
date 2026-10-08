#!/usr/bin/env python3
"""Generate Lightroom XMP presets that only set film grain, from barely
noticeable to heavy, film-like grain.

Each preset writes ONLY:
    crs:GrainAmount
    crs:GrainSize
    crs:GrainFrequency   (shown in Lightroom as "Roughness")

Run:  python3 tools/generate_grain_presets.py
Output:
    presets/Concert Grain/*.xmp
    dist/Concert-Grain-Presets.zip   (import this into Lightroom)
"""

import uuid
import zipfile

from generate_presets import ROOT, UUID_NS, alt

GROUP = "Concert Grain"
OUT_DIR = ROOT / "presets" / GROUP
ZIP_PATH = ROOT / "dist" / "Concert-Grain-Presets.zip"

# (label, amount, size, roughness). Lightroom defaults are size 25 and
# roughness 50. Size and roughness climb with amount so the heavy end reads
# as clumpy film grain rather than just stronger digital noise.
LEVELS = (
    ("Grain 1 - Whisper", 8, 15, 30),
    ("Grain 2 - Faint", 15, 18, 35),
    ("Grain 3 - Light", 22, 20, 40),
    ("Grain 4 - Fine", 30, 25, 45),
    ("Grain 5 - Medium", 40, 30, 50),
    ("Grain 6 - Visible", 50, 35, 55),
    ("Grain 7 - Strong", 62, 42, 62),
    ("Grain 8 - Heavy Film", 75, 50, 70),
)


def xmp(name, sort_name, desc, amount, size, roughness):
    preset_uuid = uuid.uuid5(UUID_NS, f"{GROUP}/{name}").hex.upper()
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
   crs:GrainAmount="{amount}"
   crs:GrainSize="{size}"
   crs:GrainFrequency="{roughness}"
   crs:HasSettings="True">
{alt("Name", name)}
{alt("ShortName", name)}
{alt("SortName", sort_name)}
{alt("Group", GROUP)}
{alt("Description", desc)}
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
"""


def build():
    presets = []
    for i, (name, amount, size, roughness) in enumerate(LEVELS, 1):
        desc = f"Grain only. Amount {amount}, Size {size}, Roughness {roughness}."
        presets.append((f"{name}.xmp", xmp(name, f"{i:02d} {name}", desc, amount, size, roughness)))

    presets.append((
        "Grain Off.xmp",
        xmp("Grain Off", "99 Grain Off", "Grain only. Sets Amount to 0 (Size and Roughness back to defaults).",
            0, 25, 50),
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
