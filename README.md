# Lightroom Presets - Stream Deck Plugin

Control Adobe **Lightroom Desktop/CC** from a Stream Deck: apply develop
presets, adjust exposure/white balance/and more with a Stream Deck+ dial,
toggle lens corrections, flag and star-rate photos, and reset/copy/paste
edit settings - all with no opening panels, no menu-diving, and no
Lightroom Classic.

```
┌─────────────┐
│   CONCERT   │
│    WARM     │
└─────────────┘
Press → Lightroom Desktop/CC applies "Concert Warm" to the selected photo
```

This targets **Lightroom Desktop/CC only**, via Lightroom's own local
**External Controller API** (a WebSocket server Lightroom itself exposes at
`ws://127.0.0.1:7682` once you enable it in Preferences). It does not use
Lightroom Classic, the Classic SDK, `.lrplugin`s, accessibility automation,
or UI scripting anywhere. See docs/PROTOCOL.md for exactly how that API was
identified and how this plugin talks to it.

> **Built without a Mac or a Lightroom license.** This project was
> developed in a Linux sandbox with no access to macOS, a physical Stream
> Deck, or a licensed Lightroom Desktop/CC install. Everything that could
> be verified without those (manifest validity, TypeScript compiling
> cleanly, the bundle running up to the point it needs Stream Deck's own
> launch arguments, protocol details cross-checked against a real
> third-party Lightroom controller plugin) has been. The one thing that
> genuinely has **not** been verified is a physical button press applying a
> real preset inside a running Lightroom Desktop/CC - that's the first
> thing to try after installing. See docs/TESTING.md.

## Requirements

- macOS 12 or later (Apple Silicon or Intel - this is a pure JavaScript/Node
  plugin with no native addons, so it runs on Stream Deck's own bundled
  Node.js runtime natively on either architecture; no universal-binary
  build step is needed).
- Elgato Stream Deck app 6.5+.
- A **Stream Deck+** is only needed for the dial-based "Adjust Develop
  Setting" action; every other action works on any Stream Deck.
- Adobe Lightroom Desktop/CC (the cloud-based app - **not** Lightroom
  Classic), with **Preferences > Interface > "Enable external
  controllers"** turned on.

## Install

1. Download/build `com.keelan182.lightroom-presets.streamDeckPlugin` (the
   repo ships a prebuilt copy at the repo root; see "Build from source"
   below to regenerate it).
2. Double-click it. The Stream Deck app installs it and shows a "Lightroom
   Presets" category with six actions (see "Using it" below).
3. In Lightroom Desktop/CC: Preferences > Interface > enable "Enable
   external controllers", then restart Lightroom.
4. Drag whichever actions you want onto buttons or (for the dial action)
   a Stream Deck+ dial, configure each one, and go - each button/dial keeps
   its own independent settings.

## Using it

- **Apply Lightroom Preset**: pick a preset, optionally mark it a favorite,
  choose how the button title should look (the preset's name, a custom
  title you type, or the preset name plus a live connection-status glyph),
  then press the button to apply that exact preset to whatever photo is
  selected in Lightroom.
- **Refresh Lightroom Presets**: re-discovers every preset from Lightroom
  and updates every button's cached list; if a button's assigned preset
  no longer exists, that button flips to an alert state telling you which
  preset went missing. The plugin also auto-refreshes its preset cache the
  first time it detects a Lightroom connection in a session.
- **Adjust Develop Setting** *(Stream Deck+ dial only)*: pick a Develop
  parameter (Exposure, Contrast, Highlights, Shadows, Whites, Blacks,
  White Balance Temperature/Tint, Vibrance, Saturation, Texture, Clarity,
  Dehaze, Sharpening, or Noise Reduction), optionally override its default
  step size, then turn the dial to adjust it on the selected photo - hold
  the dial down while turning for a 5x bigger step. The touch strip shows
  the parameter name and the delta just sent; it can't show Lightroom's
  actual current value (the API doesn't expose one - see
  docs/PROTOCOL.md). Pressing the dial just recenters the touch strip's
  cosmetic position indicator, it doesn't change anything in Lightroom.
- **Toggle Lens Correction**: flips "Lens Profile Corrections" or "Remove
  Chromatic Aberration" on/off each press. The ON/OFF shown on the button
  is this plugin's own memory of what it last set, not a live read of
  Lightroom (there's no way to query that - see docs/PROTOCOL.md), so it
  can drift if you also change the same setting inside Lightroom directly.
- **Flag & Rate Photo**: pick one action (Pick/Reject/Remove Flag, a 0-5
  star rating, or a color label) and apply it to the selected photo with
  one press.
- **Develop Utility**: reset **all** Develop adjustments on the selected
  photo (there's no per-parameter reset command), or copy/paste the whole
  edit-settings stack between photos.
- **Copy Edit Settings** / **Paste Edit Settings**: the same copy/paste
  commands as above, but as two dedicated, zero-configuration buttons -
  drag one of each onto your Stream Deck and they work immediately, no
  property inspector setup needed. (Develop Utility's copy/paste options
  still work too, for anyone who'd rather have one configurable button.)

## Known limitation: no preset folders

Lightroom's External Controller API returns a **flat** list of preset ids
and names - it does not expose which folder/group a preset belongs to.
The nested "Presets > User Presets > Concert Warm" structure some Lightroom
controller plugins imply is not something this API provides; presenting it
would mean inventing data that isn't there. Instead, presets are listed
alphabetically with an optional "★ Favorites" group (a plugin-side concept
you control, not something Lightroom reports). Full details and the
research behind this conclusion are in docs/PROTOCOL.md.

## Documentation

- **docs/ARCHITECTURE.md** - how the plugin is put together and why.
- **docs/PROTOCOL.md** - exactly what's known about Lightroom's External
  Controller API, with sources, and what's genuinely unverified.
- **docs/TROUBLESHOOTING.md** - what each on-button error state means and
  how to fix it.
- **docs/TESTING.md** - the full test plan, including the one-time critical
  acceptance test you should run first.
- **examples/preset-config.example.json** - illustrative shape of
  per-button settings and the on-disk preset cache.

## Build from source

```bash
npm install
npm run build     # rollup bundle -> com.keelan182.lightroom-presets.sdPlugin/bin/plugin.js
                   # + regenerates every icon in com.keelan182.lightroom-presets.sdPlugin/imgs/
npx @elgato/cli pack com.keelan182.lightroom-presets.sdPlugin --force
                   # -> com.keelan182.lightroom-presets.streamDeckPlugin
```

Requires Node.js 20+ (icon generation uses `zlib.crc32`, added in Node
20.12). During development, `npm run watch` rebuilds on save and restarts
the plugin inside a running Stream Deck app (requires the
[Stream Deck CLI](https://github.com/elgatosf/cli):
`npm install -g @elgato/cli`, then `streamdeck link com.keelan182.lightroom-presets.sdPlugin` once).

`npm run typecheck` runs `tsc --noEmit` under `strict` mode on its own, and
`npx @elgato/cli validate com.keelan182.lightroom-presets.sdPlugin` checks
the manifest against Elgato's own schema.

## Project layout

```
src/
  plugin.ts                    entry point / composition root
  lightroom/
    connection.ts               WebSocket client for Lightroom's External Controller API
    presetManager.ts             preset discovery + on-disk cache
    presetApplication.ts         validates + applies a preset, typed errors
    developControl.ts            adjust/toggle/command calls for Develop settings, typed errors
    paths.ts, types.ts
  actions/
    applyPreset.ts                "Apply Lightroom Preset" action
    refreshPresets.ts             "Refresh Lightroom Presets" action
    adjustDevelopSetting.ts       "Adjust Develop Setting" dial (Encoder) action
    toggleLensCorrection.ts       "Toggle Lens Correction" action
    flagAndRate.ts                "Flag & Rate Photo" action
    developUtility.ts             "Develop Utility" action (reset/copy/paste)
    copyEditSettings.ts           "Copy Edit Settings" action (dedicated, no config)
    pasteEditSettings.ts          "Paste Edit Settings" action (dedicated, no config)
com.keelan182.lightroom-presets.sdPlugin/
  manifest.json
  bin/plugin.js                 built output (committed for convenience)
  ui/*.html, ui/sdpi-components.js
  imgs/                         generated icons (scripts/generate-icons.mjs)
scripts/
  png.mjs                        dependency-free PNG encoder + tiny 2D canvas
  generate-icons.mjs             draws every icon this plugin ships
docs/
examples/
```

## License

This project's own code is MIT-licensed - see LICENSE. It vendors the
official `sdpi-components` library (also MIT-style licensed) for the
property inspector UI. See LICENSE and docs/PROTOCOL.md for the full
attribution/provenance notes on the Lightroom protocol research.
