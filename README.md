# Lightroom Presets - Stream Deck Plugin

Assign individual Adobe **Lightroom Desktop/CC** develop presets to
individual Stream Deck buttons, and apply them to the currently selected
photo with a single press - no opening the Presets panel, no searching, no
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
- Adobe Lightroom Desktop/CC (the cloud-based app - **not** Lightroom
  Classic), with **Preferences > Interface > "Enable external
  controllers"** turned on.

## Install

1. Download/build `com.keelan182.lightroom-presets.streamDeckPlugin` (the
   repo ships a prebuilt copy at the repo root; see "Build from source"
   below to regenerate it).
2. Double-click it. The Stream Deck app installs it and shows a "Lightroom
   Presets" category with two actions: **Apply Lightroom Preset** and
   **Refresh Lightroom Presets**.
3. In Lightroom Desktop/CC: Preferences > Interface > enable "Enable
   external controllers", then restart Lightroom.
4. Drag **Apply Lightroom Preset** onto a button, open its settings, and
   pick a preset from the dropdown (click "Refresh Presets" first if it's
   empty). Repeat for as many buttons as you like - each one is independent.
5. Optionally add **Refresh Lightroom Presets** to a button so you can
   re-sync the list on demand after adding/renaming presets in Lightroom.

## Using it

- **Apply Lightroom Preset**: pick a preset, optionally mark it a favorite,
  choose how the button title should look (the preset's name, a custom
  title you type, or the preset name plus a live connection-status glyph),
  then press the button to apply that exact preset to whatever photo is
  selected in Lightroom.
- **Refresh Lightroom Presets**: re-discovers every preset from Lightroom
  and updates every button's cached list; if a button's assigned preset
  no longer exists, that button flips to an alert state telling you which
  preset went missing.
- The plugin also auto-refreshes its preset cache the first time it detects
  a Lightroom connection in a session, so you don't have to remember to
  press Refresh after every plugin/Lightroom restart.

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
    paths.ts, types.ts
  actions/
    applyPreset.ts                "Apply Lightroom Preset" action
    refreshPresets.ts             "Refresh Lightroom Presets" action
com.keelan182.lightroom-presets.sdPlugin/
  manifest.json
  bin/plugin.js                 built output (committed for convenience)
  ui/apply-preset.html, ui/refresh-presets.html, ui/sdpi-components.js
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
