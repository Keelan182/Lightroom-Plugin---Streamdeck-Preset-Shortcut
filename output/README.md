# Iconic Film Stocks for Lightroom

31 presets in 25 families for **Lightroom** (the cloud-based desktop app, formerly "Lightroom CC"), **not** Lightroom Classic. Every preset is a *visual approximation* of a film stock, built only from standard Lightroom sliders: no camera profiles, LUTs, white balance or local adjustments. That keeps them portable across cameras and images.

## Import (Lightroom desktop)

1. Open a photo in **Edit**, then open the **Presets** panel.
2. Click **⋯** (top of the Presets panel) → **Import Presets…**.
3. Select **`Iconic Film Stocks.zip`**. You don't need to unzip it. You can also select individual `.xmp` files.
4. Confirm all 31 presets appear together under **Yours → Iconic Film Stocks**.

Imported presets **sync through Adobe's cloud** to Lightroom on your other computers, iPhone/iPad, Android and the web.

**One group:** every preset's `crs:Group` is **Iconic Film Stocks**, and the zip holds a single `Iconic Film Stocks/` folder with all the `.xmp` files directly inside it (no subfolders), so the whole set imports into one group. Presets within it list alphabetically, which keeps each brand's stocks next to each other; the film family is noted in each preset's description. If your Lightroom version ever files them elsewhere, select them, right-click → **Move**, and choose **Iconic Film Stocks**.

**Amount:** every preset supports Lightroom's preset **Amount** slider (0-200). Lower it to tone a look down.

## Schema / version values

No Lightroom-exported sample preset was supplied, so the files follow the current Camera Raw settings schema (`http://ns.adobe.com/camera-raw-settings/1.0/`): `crs:Version="15.4"` and `crs:ProcessVersion="15.4"` (Process Version 6, introduced with Camera Raw 15.4 in June 2023). Applying a preset therefore sets the photo to PV6, the current default for new photos. Color Grading uses the `ColorGrade*` keys, plus the `SplitToning*` keys that Color Grading reuses for shadow/highlight hue, saturation and balance.

## Presets

| Family | Preset | ISO | Type | Contrast | Saturation | Grain | Usage |
|---|---|---|---|---|---|---|---|
| Kodachrome | Kodachrome 25 | 25 | Color slide | +25 | +8 | 8/12/35 | Best on daylight scenes with strong primaries. Lower Amount for skin-heavy portraits. |
| Kodachrome | Kodachrome 64 | 64 | Color slide | +22 | +7 | 14/16/40 | The 'National Geographic' variant. Great for travel and street colour. |
| Kodachrome | Kodachrome 200 | 200 | Color slide | +18 | +4 | 28/24/55 | Grainier, warmer Kodachrome; good for available-light colour. |
| Fujifilm Velvia | Fujifilm Velvia 50 | 50 | Color slide | +35 | +25 | 5/10/30 | Landscapes. Lower Amount (40-60) for portraits; skin turns hot quickly. |
| Fujifilm Velvia | Fujifilm Velvia 100 | 100 | Color slide | +30 | +20 | 10/14/35 | Slightly more forgiving Velvia; still lower Amount for people. |
| Fujifilm Provia | Fujifilm Provia 100F | 100 | Color slide | +12 | +5 | 4/10/30 | Neutral all-rounder; good base for product work. |
| Kodak Ektachrome | Kodak Ektachrome E100 | 100 | Color slide | +15 | +8 | 8/12/35 | Clean, cool slide look; nice for snow, water and architecture. |
| Kodak Portra | Kodak Portra 160 | 160 | Color negative | -12 | -10 | 10/14/40 | Portra tolerates 1-2 stops of overexposure: brighten the image first (or shoot it bright), then apply. |
| Kodak Portra | Kodak Portra 400 | 400 | Color negative | -8 | -6 | 18/20/45 | Most versatile Portra. Overexpose/brighten before applying for the classic airy look. |
| Kodak Portra | Kodak Portra 800 | 800 | Color negative | -4 | -2 | 28/26/50 | Low-light/event Portra; warmer highlights. |
| Kodak Ektar | Kodak Ektar 100 | 100 | Color negative | +20 | +18 | 3/8/25 | Landscape/travel/architecture. Lower Amount for faces. |
| Kodak Gold | Kodak Gold 200 | 200 | Color negative | +8 | +5 | 32/30/55 | Summer, family and travel snapshots. Already warm: don't add warmth with WB on top. |
| Fujifilm Pro 400H | Fujifilm Pro 400H | 400 | Color negative | -10 | -8 | 20/20/45 | Bright, pastel weddings/portraits. Works best on slightly overexposed images. |
| Fujifilm Superia | Fujifilm Superia 400 | 400 | Color negative | +12 | +12 | 28/25/55 | Everyday Fuji consumer look; strong on foliage and skies. |
| CineStill | CineStill 800T | 800 | Color negative | +10 | +5 | 35/30/50 | Night street, neon and tungsten scenes. Leave white balance as shot; the preset adds the teal cast through grading, not WB. |
| Kodak Vision3 | Kodak Vision3 500T | 500 | Color negative | +5 | -2 | 30/25/45 | Cinematic colour with a long tonal scale; good for dusk and interiors. |
| Kodak Tri-X | Kodak Tri-X 400 | 400 | Black & white | +35 | B&W | 50/35/65 | Street and documentary. Pairs well with deliberately underexposed, contrasty light. |
| Ilford HP5 Plus | Ilford HP5 Plus 400 | 400 | Black & white | +18 | B&W | 42/30/55 | Forgiving all-round B&W. |
| Ilford FP4 Plus | Ilford FP4 Plus 125 | 125 | Black & white | +15 | B&W | 18/18/40 | Landscape and studio; smooth, detailed. |
| Ilford Pan F Plus | Ilford Pan F Plus 50 | 50 | Black & white | +30 | B&W | 6/10/25 | Bright light only; very crisp. Lower Amount if blacks block up. |
| Kodak T-Max | Kodak T-Max 100 | 100 | Black & white | +22 | B&W | 9/12/28 | Clean, modern B&W; architecture and fine detail. |
| Kodak T-Max | Kodak T-Max 400 | 400 | Black & white | +25 | B&W | 24/20/38 | Faster T-grain; cleaner than Tri-X at the same speed. |
| Ilford Delta 3200 | Ilford Delta 3200 | 3200 | Black & white | +20 | B&W | 80/55/70 | Concerts, night, moody low light. |
| Kodak Plus-X | Kodak Plus-X 125 | 125 | Black & white | +14 | B&W | 16/18/45 | Balanced vintage B&W; portraits and everyday. |
| Kodak Panatomic-X | Kodak Panatomic-X 32 | 32 | Black & white | +12 | B&W | 3/8/25 | Maximum detail; still life, landscape, architecture. |
| Kodak Double-X | Kodak Double-X 5222 | 250 | Black & white | +12 | B&W | 45/40/60 | Film-noir and cinematic portraits. Box speed 250 (daylight). |
| Kodak Aerochrome | Kodak Aerochrome | — | Specialty | +20 | +15 | 15/20/45 | Use on scenes with lots of foliage in sun. Results vary strongly by image; reduce Amount if non-foliage areas go too pink. |
| Kodak High-Speed Infrared | Kodak High-Speed Infrared HIE | — | Specialty | +25 | B&W | 85/60/75 | Sunny landscapes with foliage and blue sky. |
| Lomochrome Purple | Lomochrome Purple | — | Specialty | +15 | +10 | 25/25/50 | Foliage-heavy scenes. Highly image-dependent; dial Amount to taste. |
| Polaroid | Polaroid | — | Specialty | -20 | -12 | 30/40/70 | Casual, nostalgic portraits and still life. |
| Fujifilm Instax | Fujifilm Instax | — | Specialty | +15 | +6 | 18/25/50 | Party and lifestyle snaps; brighter skin. |

Grain is shown as Amount/Size/Roughness.

## Trait → setting mapping

Quoted traits come verbatim from `film_stocks.txt`. Bracketed rows are derived notes, such as how ISO variants within a family are told apart. Values are the actual preset values.

### Kodachrome 25

| Trait | Settings |
|---|---|
| “Deep, rich reds and yellows” | HSL Sat Red +20; HSL Sat Yellow +18; Calib Red Sat +10; HSL Hue Yellow -6 |
| “strong contrast” | Contrast +25; Blacks -16; Point curve 0→0 64→54 128→128 192→204 255→252 |
| “"warm but crisp" rendering” | Red curve 0→0 128→132 255→255; Blue curve 0→0 128→124 255→250; Grade Highlight Hue 45; Grade Highlight Sat 8; Texture +12 |
| ISO 25: finest grain and highest acutance of the three | GrainAmount 8; Sharpness 55 |

### Kodachrome 64

| Trait | Settings |
|---|---|
| “Deep, rich reds and yellows” | HSL Sat Red +22; HSL Sat Yellow +20; Calib Red Sat +12; HSL Hue Orange -5 |
| “strong contrast” | Contrast +22; Blacks -14; Point curve 0→0 64→56 128→128 192→202 255→252 |
| “"warm but crisp" rendering” | Red curve 0→0 128→133 255→255; Green curve 0→0 128→129 255→255; Blue curve 0→0 128→123 255→248; Grade Highlight Hue 42; Grade Highlight Sat 10 |
| “Associated with National Geographic” | warmest highlights of the family |
| ISO 64: slightly more grain than 25 | GrainAmount 14 |

### Kodachrome 200

| Trait | Settings |
|---|---|
| “Deep, rich reds and yellows” | HSL Sat Red +16; HSL Sat Yellow +14; Calib Red Sat +8 |
| “strong contrast” | Contrast +18; Point curve 0→4 64→58 128→129 192→200 255→250 |
| “"warm but crisp" rendering” | Red curve 0→0 128→134 255→255; Blue curve 0→0 128→121 255→246; Grade Midtone Hue 45; Grade Midtone Sat 4 |
| ISO 200: lower contrast, warmer/yellower, clearly visible grain | Contrast +18; GrainAmount 28; GrainSize 24 |

### Fujifilm Velvia 50

| Trait | Settings |
|---|---|
| “Extreme saturation, especially in greens, blues, and magentas” | Saturation +25; Vibrance +15; HSL Sat Green +30; HSL Sat Blue +25; HSL Sat Magenta +25; Calib Blue Sat +25 |
| “high contrast and a narrow exposure latitude” | Contrast +35; Blacks -25; Point curve 0→0 64→46 128→128 192→212 255→255 |
| “Very fine grain at ISO 50” | GrainAmount 5; GrainSize 10 |
| “Can shift warm/magenta in shade” | Grade Shadow Hue 320; Grade Shadow Sat 6; Calib Shadow Tint +4 |

### Fujifilm Velvia 100

| Trait | Settings |
|---|---|
| “Extreme saturation, especially in greens, blues, and magentas” | Saturation +20; HSL Sat Green +22; HSL Sat Blue +20; HSL Sat Magenta +20 |
| “high contrast and a narrow exposure latitude” | Contrast +30; Blacks -20 |
| “Can shift warm/magenta in shade” | Grade Shadow Hue 330; Grade Shadow Sat 4 |
| ISO 100: a notch less saturation/contrast than 50, slightly more grain | Saturation +20; Contrast +30; GrainAmount 10 |

### Fujifilm Provia 100F

| Trait | Settings |
|---|---|
| “Neutral, accurate color with moderate saturation” | Saturation +5; Vibrance +5; HSL Sat Blue +5; no colour grading |
| “extremely fine grain” | GrainAmount 4; GrainSize 10 |
| “A more "faithful" counterpart to Velvia” | Contrast +12; Point curve 0→0 64→59 128→128 192→198 255→255 |

### Kodak Ektachrome E100

| Trait | Settings |
|---|---|
| “Cleaner, cooler, more neutral palette than Kodachrome” | Red curve 0→0 128→126 255→253; Blue curve 0→0 128→131 255→255; Grade Highlight Hue 210; Grade Shadow Hue 220 |
| “slightly blue bias” | HSL Sat Blue +12; HSL Sat Aqua +10; Calib Blue Sat +8 |
| “Fine grain and good sharpness” | GrainAmount 8; Sharpness 55; Texture +10 |

### Kodak Portra 160

| Trait | Settings |
|---|---|
| “Soft contrast, muted pastels” | Contrast -12; Point curve 0→14 64→70 128→130 192→194 255→246; Saturation -10; HSL Sat Green -25; HSL Sat Yellow -15 |
| “natural, smooth skin tones” | HSL Hue Orange +3; HSL Lum Orange +6; Clarity -5; Texture -6 |
| “keeps highlights smooth” | Highlights -28; Whites -10; Point curve 0→14 64→70 128→130 192→194 255→246 |
| ISO 160: lowest contrast/saturation, finest grain of the three | Contrast -12; Saturation -10; GrainAmount 10 |

### Kodak Portra 400

| Trait | Settings |
|---|---|
| “Soft contrast, muted pastels” | Contrast -8; Point curve 0→12 64→68 128→130 192→196 255→248; Saturation -6; HSL Sat Green -20 |
| “natural, smooth skin tones” | HSL Hue Orange +4; HSL Lum Orange +5; Clarity -3 |
| “Very fine grain for its speed” | GrainAmount 18; GrainSize 20 |
| ISO 400: a little more contrast, colour and grain than 160 | Contrast -8; Saturation -6; GrainAmount 18 |

### Kodak Portra 800

| Trait | Settings |
|---|---|
| “Soft contrast, muted pastels” | Contrast -4; Saturation -2 |
| “natural, smooth skin tones” | HSL Hue Orange +4; HSL Lum Orange +4 |
| “Very fine grain for its speed” | GrainAmount 28; GrainSize 26 |
| ISO 800: most contrast, colour, warmth and grain of the family | Contrast -4; Grade Highlight Sat 10; GrainAmount 28 |

### Kodak Ektar 100

| Trait | Settings |
|---|---|
| “finest-grained color negative films ever made” | GrainAmount 3; GrainSize 8 |
| “very high sharpness” | Sharpness 65; Sharpen Detail 45; Texture +15 |
| “Saturated, punchy colors with strong reds” | Saturation +18; HSL Sat Red +20; Calib Red Sat +12; Contrast +20 |
| “slight warm cast” | Red curve 0→0 128→132 255→255; Blue curve 0→0 128→125 255→252; Grade Global Hue 35; Grade Global Sat 4 |
| “Less forgiving with skin tones” | HSL Hue Red -3; no skin-protecting orange tweaks |

### Kodak Gold 200

| Trait | Settings |
|---|---|
| “Warm, golden-yellow cast” | Red curve 0→0 128→134 255→255; Blue curve 0→0 128→118 255→240; Grade Highlight Hue 50; Grade Highlight Sat 15; Grade Midtone Hue 45; Grade Midtone Sat 10 |
| “medium saturation” | Saturation +5; Vibrance +8; HSL Sat Yellow +15 |
| “visible but pleasant grain” | GrainAmount 32; GrainSize 30; Grain Roughness 55 |
| “nostalgic, "family photo" look” | Blacks +6; Point curve 0→8 64→64 128→130 192→198 255→250; Vignette -10 |

### Fujifilm Pro 400H

| Trait | Settings |
|---|---|
| “pastel, airy colors” | Saturation -8; Exposure +0.15; Shadows +18; Point curve 0→16 64→74 128→134 192→198 255→248 |
| “cool-leaning greens” | HSL Hue Green +20; HSL Hue Yellow +10; Calib Green Hue +5 |
| “cyan-blue shadows” | Blue curve 0→10 64→70 128→130 255→252; Green curve 0→2 128→130 255→255; Grade Shadow Hue 195; Grade Shadow Sat 15 |
| “improved skin-tone” | HSL Lum Orange +8; HSL Sat Orange -8; Clarity -8 |

### Fujifilm Superia 400

| Trait | Settings |
|---|---|
| “more saturated” | Saturation +12; Vibrance +8 |
| “punchy greens and blues” | HSL Sat Green +20; HSL Sat Blue +15; Calib Green Sat +8; Calib Blue Sat +8 |
| “slightly cool palette versus Kodak” | Green curve 0→0 128→130 255→255; Blue curve 0→4 128→129 255→254; Grade Shadow Hue 175; Calib Shadow Tint -4 |

### CineStill 800T

| Trait | Settings |
|---|---|
| “renders cool/teal in daylight” | Blue curve 0→6 128→134 255→250; Grade Shadow Hue 190; Grade Shadow Sat 20; Grade Midtone Hue 200; Calib Blue Hue -15 |
| “red-orange halation glow around bright highlights” | Grade Highlight Hue 20; Grade Highlight Sat 15; Red curve 0→0 128→126 192→196 255→255; HSL Lum Red +10; Dehaze -8; Highlights -30 |
| “Cinematic night-city aesthetic” | HSL Hue Green +30; Clarity -10; Vignette -12 |

### Kodak Vision3 500T

| Trait | Settings |
|---|---|
| “Motion-picture stock repackaged for stills” | Point curve 0→10 64→64 128→128 192→196 255→248; Highlights -25; Shadows +12; flat, log-like cinema curve |
| “Tungsten-balanced, so it renders cool/teal in daylight” | Grade Shadow Hue 190; Grade Shadow Sat 14; Grade Midtone Hue 195; Calib Blue Hue -10 |
| With remjet intact: no halation, cleaner highlights than CineStill | Dehaze 0; Grade Highlight Sat 6 |

### Kodak Tri-X 400

| Trait | Settings |
|---|---|
| “Prominent grain” | GrainAmount 50; GrainSize 35; Grain Roughness 65 |
| “high, punchy contrast” | Contrast +35; Blacks -20; Whites +15; Point curve 0→0 64→48 128→130 192→212 255→255 |
| “Gritty, classic documentary look” | Clarity +20; Texture +15 |

### Ilford HP5 Plus 400

| Trait | Settings |
|---|---|
| “Smoother tonality and slightly finer grain than Tri-X” | Contrast +18; GrainAmount 42; GrainSize 30; Point curve 0→4 64→56 128→128 192→204 255→252 |
| “very wide latitude” | Highlights -15; Shadows +10 |
| “produces rich midtones” | Clarity +8; Point curve 0→4 64→56 128→128 192→204 255→252 |

### Ilford FP4 Plus 125

| Trait | Settings |
|---|---|
| “Fine grain, high sharpness, and smooth gradation” | GrainAmount 18; Sharpness 60; Texture +12; Point curve 0→0 64→58 128→128 192→202 255→255 |
| “Favored for landscape and studio work” | B&W Mix Green -8; B&W Mix Blue -5 |

### Ilford Pan F Plus 50

| Trait | Settings |
|---|---|
| “Pan F is especially fine-grained and contrasty at ISO 50” | GrainAmount 6; Contrast +30; Blacks -18; Point curve 0→0 64→50 128→128 192→210 255→255 |
| “high sharpness” | Sharpness 70; Sharpen Detail 50; Texture +18 |
| extended red sensitivity: reds/oranges render lighter | B&W Mix Red +8; B&W Mix Orange +10 |

### Kodak T-Max 100

| Trait | Settings |
|---|---|
| “T-grain (tabular crystal) technology gives very fine grain and high sharpness” | GrainAmount 9; Grain Roughness 28; Sharpness 65; Texture +15 |
| “Cleaner, more modern look than Tri-X” | Clarity +6; Point curve 0→0 64→54 128→128 192→206 255→255 |
| “Can be contrasty” | Contrast +22; Whites +10 |

### Kodak T-Max 400

| Trait | Settings |
|---|---|
| “very fine grain and high sharpness” | GrainAmount 24; Grain Roughness 38; Sharpness 55 |
| “Can be contrasty and less forgiving if mishandled” | Contrast +25; Blacks -15; Point curve 0→0 64→52 128→128 192→208 255→255 |
| ISO 400: more grain and contrast than T-Max 100, still tighter than Tri-X | GrainAmount 24; Contrast +25 |

### Ilford Delta 3200

| Trait | Settings |
|---|---|
| “Very pronounced, stylized grain” | GrainAmount 80; GrainSize 55; Grain Roughness 70 |
| “low-light capability” | Shadows +15; Point curve 0→6 64→56 128→128 192→204 255→250 |
| “True speed is closer to ISO 1000-1600” | no exposure change: brighten before applying if underexposed |

### Kodak Plus-X 125

| Trait | Settings |
|---|---|
| “classic medium-speed, balanced look” | Contrast +14; Point curve 0→2 64→58 128→128 192→200 255→254; B&W Mix Blue +6 |
| “fine grain” | GrainAmount 16; GrainSize 18 |

### Kodak Panatomic-X 32

| Trait | Settings |
|---|---|
| “extraordinarily fine grain” | GrainAmount 3; GrainSize 8 |
| “very high resolving power” | Sharpness 75; Sharpen Radius +0.6; Sharpen Detail 60; Texture +20 |
| long, gentle tonal scale | Contrast +12; Point curve 0→0 64→60 128→128 192→198 255→255 |

### Kodak Double-X 5222

| Trait | Settings |
|---|---|
| “Moderate contrast” | Contrast +12; Point curve 0→4 64→56 128→128 192→202 255→248 |
| “vintage cinematic grain structure” | GrainAmount 45; GrainSize 40; Grain Roughness 60 |
| “classic black-and-white cinema” | Highlights -18; Vignette -15 |

### Kodak Aerochrome

| Trait | Settings |
|---|---|
| “Foliage renders in vivid red, pink, and magenta” | HSL Hue Green -100; HSL Hue Yellow -100; Calib Green Hue -100; Calib Red Hue -50; Red curve 0→0 64→72 128→142 255→255; Green curve 0→0 128→116 255→245; Grade Midtone Hue 330; Grade Midtone Sat 15 |
| “Surreal, otherworldly palette” | Saturation +15; HSL Sat Green +40; HSL Sat Yellow +40; Grade Highlight Hue 340 |
| skies kept deep blue | HSL Sat Blue +20; HSL Lum Blue -15; Grade Shadow Hue 240 |

### Kodak High-Speed Infrared HIE

| Trait | Settings |
|---|---|
| “white "glowing" foliage” | B&W Mix Green +80; B&W Mix Yellow +60; Whites +20 |
| “dark skies” | B&W Mix Blue -80; B&W Mix Aqua -60; B&W Mix Purple -40 |
| “dreamy halation effect” | Dehaze -15; Clarity -20; Texture -10 |
| “Extremely heavy grain” | GrainAmount 85; GrainSize 60; Grain Roughness 75 |

### Lomochrome Purple

| Trait | Settings |
|---|---|
| “Shifts greens to purple and magenta” | HSL Hue Green +100; HSL Hue Aqua +100; Calib Green Hue +100; Green curve 0→0 128→118 255→248; Grade Midtone Hue 290; Grade Midtone Sat 15 |
| “blues to different hues” | HSL Hue Blue -100; Calib Blue Hue +50 |
| “variable, unpredictable results” | result depends heavily on scene colour; adjust Amount |

### Polaroid

| Trait | Settings |
|---|---|
| “soft focus” | Clarity -20; Texture -15; Dehaze -10; Sharpness 10 |
| “lower contrast” | Contrast -20; Blacks +20; Whites -15; Point curve 0→28 64→78 128→132 192→190 255→236 |
| “color shifts” | Red curve 0→6 255→250; Blue curve 0→14 128→130 255→236; Grade Shadow Hue 185; Grade Highlight Hue 50; HSL Hue Green +15 |
| “visible chemical texture” | GrainAmount 30; GrainSize 40; Grain Roughness 70 |

### Fujifilm Instax

| Trait | Settings |
|---|---|
| “crisper, higher contrast” | Contrast +15; Clarity +5; Sharpness 45 |
| “more modern color” | Saturation +6; Vibrance +10; HSL Sat Aqua +15; HSL Lum Orange +8 |
| “framed look” | Vignette -12; frame itself not possible |

## Approximation limits

These presets are approximations. Lightroom presets can't reproduce spatial effects (glow, halation, borders, emulsion damage), infrared data, or the exact dye chemistry of a process. Specifically:

- **All stocks:** real film response depends on exposure, development and scanning. A preset re-maps tones and colours of a digital file and can't add dynamic range that wasn't captured.
- **Kodachrome 25:** K-14's specific dye response and archival stability cannot be reproduced with sliders; this is a tonal/colour approximation.
- **Kodachrome 64:** K-14 dye response approximated; no grain-structure or dye-cloud emulation beyond Lightroom Grain.
- **Kodachrome 200:** K-14 dye response approximated.
- **Fujifilm Velvia 50:** Reciprocity failure on long exposures is exposure-dependent and not emulated.
- **Fujifilm Velvia 100:** Reciprocity behaviour not emulated.
- **Kodak Portra 160:** Negative-film exposure latitude cannot be added after capture; the highlight roll-off only mimics it.
- **Kodak Portra 400:** Exposure latitude not reproducible after capture.
- **Kodak Portra 800:** Exposure latitude not reproducible after capture.
- **Fujifilm Pro 400H:** The fourth colour layer's fluorescent-light behaviour is not emulated.
- **CineStill 800T:** Halation is a spatial glow around bright sources; Lightroom has no spatial bloom, so it is approximated with warm highlight grading and negative Dehaze/Clarity.
- **Kodak Vision3 500T:** ECN-2 print-film interaction is not modelled.
- **Kodak Tri-X 400:** Push-processing (1600-3200) response is not a separate preset; add contrast/grain manually.
- **Kodak Aerochrome:** Real Aerochrome records near-infrared reflectance; a visible-light file has no IR channel, so foliage is recoloured by hue, not by IR. Green objects that aren't plants also turn red/magenta, and foliage reaches orange-red/magenta rather than pure crimson.
- **Kodak High-Speed Infrared HIE:** No real IR data: foliage brightens by colour, not IR reflectance, so green non-plant objects also glow and dark foliage in shade stays darker than on HIE.
- **Kodak High-Speed Infrared HIE:** HIE's halation (no anti-halation backing) is a spatial glow; approximated with negative Dehaze/Clarity only.
- **Lomochrome Purple:** HSL can move a hue band only ~30 degrees, so greens are pushed through cyan/blue with Calibration and grading rather than truly remapped to purple. Expect blue-violet foliage rather than Lomochrome's full purple.
- **Polaroid:** Chemical texture/emulsion marks are spatial artefacts; only Lightroom Grain is used.
- **Polaroid:** The physical white frame cannot be added by a preset (no borders in Lightroom).
- **Fujifilm Instax:** The physical Instax frame cannot be added by a preset.

**Flagged as weak approximations:** CineStill 800T, Kodak Aerochrome, Kodak High-Speed Infrared HIE, Lomochrome Purple, Polaroid.

## Usage notes

- **Kodachrome 25:** Best on daylight scenes with strong primaries. Lower Amount for skin-heavy portraits.
- **Kodachrome 64:** The 'National Geographic' variant. Great for travel and street colour.
- **Kodachrome 200:** Grainier, warmer Kodachrome; good for available-light colour.
- **Fujifilm Velvia 50:** Landscapes. Lower Amount (40-60) for portraits; skin turns hot quickly.
- **Fujifilm Velvia 100:** Slightly more forgiving Velvia; still lower Amount for people.
- **Fujifilm Provia 100F:** Neutral all-rounder; good base for product work.
- **Kodak Ektachrome E100:** Clean, cool slide look; nice for snow, water and architecture.
- **Kodak Portra 160:** Portra tolerates 1-2 stops of overexposure: brighten the image first (or shoot it bright), then apply.
- **Kodak Portra 400:** Most versatile Portra. Overexpose/brighten before applying for the classic airy look.
- **Kodak Portra 800:** Low-light/event Portra; warmer highlights.
- **Kodak Ektar 100:** Landscape/travel/architecture. Lower Amount for faces.
- **Kodak Gold 200:** Summer, family and travel snapshots. Already warm: don't add warmth with WB on top.
- **Fujifilm Pro 400H:** Bright, pastel weddings/portraits. Works best on slightly overexposed images.
- **Fujifilm Superia 400:** Everyday Fuji consumer look; strong on foliage and skies.
- **CineStill 800T:** Night street, neon and tungsten scenes. Leave white balance as shot; the preset adds the teal cast through grading, not WB.
- **Kodak Vision3 500T:** Cinematic colour with a long tonal scale; good for dusk and interiors.
- **Kodak Tri-X 400:** Street and documentary. Pairs well with deliberately underexposed, contrasty light.
- **Ilford HP5 Plus 400:** Forgiving all-round B&W.
- **Ilford FP4 Plus 125:** Landscape and studio; smooth, detailed.
- **Ilford Pan F Plus 50:** Bright light only; very crisp. Lower Amount if blacks block up.
- **Kodak T-Max 100:** Clean, modern B&W; architecture and fine detail.
- **Kodak T-Max 400:** Faster T-grain; cleaner than Tri-X at the same speed.
- **Ilford Delta 3200:** Concerts, night, moody low light.
- **Kodak Plus-X 125:** Balanced vintage B&W; portraits and everyday.
- **Kodak Panatomic-X 32:** Maximum detail; still life, landscape, architecture.
- **Kodak Double-X 5222:** Film-noir and cinematic portraits. Box speed 250 (daylight).
- **Kodak Aerochrome:** Use on scenes with lots of foliage in sun. Results vary strongly by image; reduce Amount if non-foliage areas go too pink.
- **Kodak High-Speed Infrared HIE:** Sunny landscapes with foliage and blue sky.
- **Lomochrome Purple:** Foliage-heavy scenes. Highly image-dependent; dial Amount to taste.
- **Polaroid:** Casual, nostalgic portraits and still life.
- **Fujifilm Instax:** Party and lifestyle snaps; brighter skin.

## Rebuilding

```sh
python3 build_presets.py
```

Each build creates fresh random UUIDs (uuid4). If you re-import a rebuilt set, delete the old groups in Lightroom first to avoid duplicates.
