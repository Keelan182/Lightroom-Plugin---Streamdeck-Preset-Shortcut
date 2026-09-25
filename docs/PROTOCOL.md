# Lightroom Desktop/CC External Controller API - protocol notes

This document records what is actually known about Lightroom's local
"External Controller API", where that knowledge came from, and exactly
which parts are Adobe-documented vs. reverse-engineered/observed. It exists
so nobody has to re-derive this from scratch, and so the provenance of every
claim is auditable.

## What this is (and isn't)

- It **is** a feature Adobe ships inside Lightroom Desktop/CC itself: a
  local WebSocket server the app starts when you enable **Preferences >
  Interface > "Enable external controllers"**.
- It **is not** Lightroom Classic, the Lightroom Classic SDK, the Lightroom
  Classic `LrDevelopController` Lua API, or the cloud "Lightroom API" /
  "Lightroom Partner APIs" (the OAuth REST API for Creative Cloud-stored
  photos at `developer.adobe.com/lightroom`). Those are three unrelated
  Adobe surfaces that are easy to conflate by name alone.
- Adobe has not published a public schema/reference for this specific local
  API (unlike Lightroom Classic's published "Externally Controlling
  Lightroom" SDK addendum). Everything below marked "observed" comes from
  third-party reverse engineering, not an Adobe spec.

## Endpoint

- Default: `ws://127.0.0.1:7682`.
- If port 7682 is unavailable, Lightroom picks another port and records it
  somewhere under `~/Library/Application Support/Adobe/Lightroom CC/Connections`
  on macOS. The exact file name/schema inside that folder is undocumented;
  this plugin best-effort-scans that folder for a `*.json` file containing a
  `port`/`Port`/`websocketPort`/`webSocketPort` key and falls back to 7682
  if it can't find or parse one (`src/lightroom/connection.ts#detectPort`).

## Message envelope

Every request is a JSON object sent as a single WebSocket text frame:

```json
{ "requestId": "<uuid>", "object": null, "message": "<command>", "params": [] }
```

Responses correlate back to the request via `requestId` and look like:

```json
{ "requestId": "<uuid>", "success": true, "response": <any> }
```

This plugin's `LightroomConnection` (`src/lightroom/connection.ts`) keeps a
`Map<requestId, pendingPromise>` and resolves/rejects the matching promise
when a message with that `requestId` arrives, so multiple requests can be in
flight concurrently. This is an improvement over the reference
implementation we studied (see "Prior art" below), which sent a request and
then did a single blocking read of the very next frame - correct only if
requests are never issued concurrently and every response fits in one frame.

## Pairing / registration

Before any other command works, the client must send:

```json
{ "requestId": "<uuid>", "object": null, "message": "register", "params": ["<app name>", "<app version>", <previous client GUID or null>] }
```

Observed behavior: the first time an unrecognized `(app name, app version)`
pair registers, Lightroom shows the user a pairing dialog ("Allow this
controller to connect?"); the request does not get a response until the
user clicks **Allow**. On success, `response` is an array whose first
element is a client GUID; resending that same GUID on a later `register`
call appears to let Lightroom recognize a previously-approved client
without another dialog, though this is not documented behavior and could
change. This plugin persists that GUID to
`~/Library/Application Support/com.keelan182.lightroom-presets/connection-state.json`
so pairing survives Stream Deck/plugin restarts, not just process-lifetime
(an improvement over the reference implementation, which only kept the GUID
in memory).

Because a real "Allow" click can take any amount of time, this plugin uses a
longer timeout for `register` (12s) than for ordinary requests (8s), and
surfaces a distinct `unresponsive` connection status (rather than a generic
failure) so the property inspector can tell the user to check for an open
pairing dialog.

## Preset discovery

Two commands, both **observed**, not documented by Adobe:

- `getPresetIDs` (no params) - returns every preset's id. The response
  shape is not consistent; it has been observed as a plain array of id
  strings, a JSON-encoded string containing that array, an array containing
  one nested array of ids, or an object with the array under an
  unpredictable property name. `extractPresetIds()` in
  `src/lightroom/presetManager.ts` defensively unwraps all of these.
- `getPresetName` with `params: [presetId]` - returns that single preset's
  display name (a string, sometimes wrapped in a 1-element array).

There is **no folder/group/category field anywhere in these responses**.
Requirement #4's nested "Presets > User Presets > Concert Warm" hierarchy is
not something Lightroom's External Controller API exposes at all, at least
as of this writing - the ids and names really are a flat list. This plugin
therefore presents presets as a flat, alphabetically-sorted list with an
optional "★ Favorites" group layered on top (favorites are a
plugin-side concept, stored in this plugin's own global settings, not
something Lightroom reports). If Adobe adds folder metadata to this API in
the future, `PresetManager` is the only place that would need to change.

Because each preset's name requires its own round trip, this plugin fetches
names with a small concurrency window (4 at a time, 15ms stagger between
batches) rather than the fully serial one-at-a-time-with-50ms-sleep approach
we observed elsewhere - meaningfully faster for large (100+) preset
libraries while still being gentle on the socket.

## Applying a preset

`applyPreset` with `params: [presetId]`. Observed to apply that preset to
whatever photo is currently selected/active in Lightroom. There is no
documented, structured error for "no photo is selected" - a failure here
surfaces only as a missing/failed response or a `success: false`, which
this plugin surfaces to the user as a generic "Lightroom did not confirm
applying this preset" message rather than a precise "no photo selected"
message it cannot actually verify. This is a known, documented limitation
(see docs/TROUBLESHOOTING.md), not a claim that the plugin can detect that
specific case.

## Develop-parameter, toggle, and workflow commands

Beyond presets, the same API exposes continuous Develop-parameter
adjustment, on/off settings, and a handful of parameter-less workflow
commands, all used by the "Adjust Develop Setting", "Toggle Lens
Correction", "Flag & Rate Photo", and "Develop Utility" actions. The exact
parameter-name strings below are **observed**, not documented by Adobe -
sourced from a real, working third-party plugin's code (see "Prior art"
below), the same way the preset commands were.

**Continuous adjustments** - `increment`/`decrement` with
`params: [parameterName, amount]`, where `amount` is a positive magnitude
in Lightroom's own units for that parameter (e.g. Exposure moves in whole
stops, so `1.0` is a full stop; Temperature is in Kelvin, so a step of
`50` is a modest nudge):

| Group | Parameter name | Label |
|---|---|---|
| Light | `Exposure2012` | Exposure |
| Light | `Contrast2012` | Contrast |
| Light | `Highlights2012` | Highlights |
| Light | `Shadows2012` | Shadows |
| Light | `Whites2012` | Whites |
| Light | `Blacks2012` | Blacks |
| Color | `Temperature` | White Balance: Temperature |
| Color | `Tint` | White Balance: Tint |
| Color | `Vibrance` | Vibrance |
| Color | `Saturation` | Saturation |
| Effects | `Texture` | Texture |
| Effects | `Clarity2012` | Clarity |
| Effects | `Dehaze` | Dehaze |
| Detail | `Sharpness` | Sharpening |
| Detail | `LuminanceSmoothing` | Noise Reduction: Luminance |
| Detail | `ColorNoiseReduction` | Noise Reduction: Color |

This plugin sends **one batched `increment`/`decrement` call per dial
rotation event**, sized by however many ticks were turned
(`amount = ticks * stepSize`), rather than one call per tick - an
improvement over the reference project, which looped a separate WebSocket
call per tick.

**On/off settings** - `setValue` with `params: [parameterName, 0 | 1]`.
There is no corresponding "get" command, so a value set this way can never
be read back - `Toggle Lens Correction`'s on-screen ON/OFF state is only
what this plugin itself last set, not a live read of Lightroom's actual
state (see docs/TROUBLESHOOTING.md).

| Parameter name | Label |
|---|---|
| `LensProfileEnable` | Lens Profile Corrections |
| `AutoLateralCA` | Remove Chromatic Aberration |

**Parameter-less commands** - just `{ "message": "<name>" }`, no params:

| Command | Label |
|---|---|
| `flagPick` / `flagReject` / `flagUnflag` | Flag: Pick / Reject / Remove Flag |
| `rating0` … `rating5` | Rating: 0–5 stars |
| `colorLabelRed` / `Yellow` / `Green` / `Blue` / `Purple` / `None` | Color Label |
| `resetAllDevelopAdjustments` | Reset **all** Develop settings on the photo - there is no per-parameter reset command |
| `copyEditSettings` / `pasteEditSettings` | Copy/paste the whole edit-settings stack between photos |

As with `applyPreset`, none of these return a structured success/failure
signal beyond the generic `success` flag - Lightroom confirms it accepted
the command, not that a photo was selected or that the value visibly
changed.

## Prior art / attribution

Understanding of this protocol was built by reading the publicly available
source of **adamkarnowka/loupedeck-lightroom-cc**
(https://github.com/adamkarnowka/loupedeck-lightroom-cc), a third-party
Loupedeck plugin, plus public discussion of Lightroom's "Enable third-party
controllers" feature (Adobe community threads, the `electerious/lightroom-controller`
project, and the `rsjaffe/MIDI2LR` project's discussion of the same API).
No source code from any of those projects is included in this repository -
this plugin's TypeScript implementation
(`src/lightroom/connection.ts`, `src/lightroom/presetManager.ts`,
`src/lightroom/presetApplication.ts`) was written from scratch against the
*facts* above (message names, field shapes, endpoint, pairing flow), which
are protocol/interoperability information rather than copyrightable
expression. The loupedeck-lightroom-cc README states it is MIT-licensed,
but the repository had no LICENSE file at the time of this review, so
nothing from it has been copied regardless.
