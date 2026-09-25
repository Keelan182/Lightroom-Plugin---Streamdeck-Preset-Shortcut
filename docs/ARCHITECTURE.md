# Architecture

```
Stream Deck app (Elgato)
   │  Stream Deck plugin protocol (local WebSocket managed by @elgato/streamdeck)
   ▼
This plugin - a single long-lived Node.js process (src/plugin.ts)
   │
   ├── LightroomConnection            (src/lightroom/connection.ts)
   │      - Owns the one persistent WebSocket to Lightroom's External
   │        Controller API (ws://127.0.0.1:7682, or a discovered port).
   │      - register handshake + pairing-GUID persistence.
   │      - request/response correlation by requestId (supports concurrent
   │        in-flight requests).
   │      - liveness polling (is Lightroom's process even running?),
   │        reconnect with exponential backoff, and a 5-state status:
   │        not-running / connecting / connected / disconnected / unresponsive.
   │      - Emits "status" events; nothing above this layer talks sockets.
   │
   ├── PresetManager                  (src/lightroom/presetManager.ts)
   │      - refresh(): getPresetIDs -> getPresetName (bounded concurrency)
   │        -> sorted LightroomPreset[] -> cached to disk.
   │      - getPresets()/findById()/search() read the in-memory cache.
   │      - Loads its disk cache on startup so buttons show real preset
   │        names immediately, before Lightroom even needs to be reachable.
   │      - No folder/hierarchy modeling - Lightroom's API doesn't expose
   │        one (see docs/PROTOCOL.md).
   │
   ├── PresetApplicationService       (src/lightroom/presetApplication.ts)
   │      - apply(presetId): validates a preset id is configured and known,
   │        checks LightroomConnection's status, calls "applyPreset", and
   │        translates every failure mode into a typed
   │        PresetApplicationError the UI layer can render without knowing
   │        anything about sockets or JSON shapes.
   │
   ├── DevelopControlService          (src/lightroom/developControl.ts)
   │      - adjustParameter(id, amount): "increment"/"decrement" for
   │        continuous Develop settings (exposure, white balance, etc.).
   │      - setToggle(id, 0|1): "setValue" for on/off settings (lens
   │        profile corrections, chromatic aberration removal).
   │      - sendCommand(id): fire-and-forget commands (flagging, rating,
   │        color labels, reset/copy/paste).
   │      - Same connection-status checks and typed-error pattern as
   │        PresetApplicationService, kept as a separate class because
   │        presets and live Develop-parameter control are different
   │        concerns that happen to share one connection.
   │      - DEVELOP_PARAMETERS/DEVELOP_TOGGLES/DEVELOP_COMMANDS export the
   │        fixed catalogs of supported parameter names (see
   │        docs/PROTOCOL.md for where those exact strings came from).
   │
   └── Stream Deck actions            (src/actions/)
          ├── ApplyPresetAction    (com.keelan182.lightroom-presets.apply-preset)
          │      - Per-instance settings: presetId, presetName (fallback
          │        label), titleMode, customTitle. Every button keeps its
          │        own settings object - Stream Deck already isolates these
          │        per action instance, so button 1 and button 2 never
          │        share state.
          │      - onKeyDown -> PresetApplicationService.apply(), then
          │        showOk()/showAlert() + a temporary title flash.
          │      - onSendToPlugin handles the property inspector's
          │        "getPresets" (data source), "refreshPresets", and
          │        "toggleFavorite" messages.
          │      - reconcileAssignments()/refreshTitlesForStatus() are
          │        called from outside (by RefreshPresetsAction and
          │        plugin.ts) to update every visible button after a
          │        refresh or a connection-status change.
          │
          ├── RefreshPresetsAction (com.keelan182.lightroom-presets.refresh-presets)
          │      - onKeyDown -> PresetManager.refresh(), then asks
          │        ApplyPresetAction to flag any button whose preset id
          │        disappeared.
          │
          ├── AdjustDevelopSettingAction (com.keelan182.lightroom-presets.adjust-develop-setting)
          │      - A Stream Deck+ **dial (Encoder)** action, not a button -
          │        see "Dial and touch strip support" below.
          │
          ├── ToggleLensCorrectionAction (com.keelan182.lightroom-presets.toggle-lens-correction)
          │      - onKeyDown -> DevelopControlService.setToggle(), flips a
          │        locally-tracked isOn flag and shows it in the title
          │        (ON/OFF) - Lightroom's API can't be queried for the real
          │        current value, so this is a best-effort mirror, not a
          │        live read (see docs/PROTOCOL.md).
          │
          ├── FlagAndRateAction (com.keelan182.lightroom-presets.flag-and-rate)
          │      - onKeyDown -> DevelopControlService.sendCommand() for
          │        whichever flag/rating/color-label command is configured.
          │
          └── DevelopUtilityAction (com.keelan182.lightroom-presets.develop-utility)
                 - onKeyDown -> DevelopControlService.sendCommand() for
                   resetAllDevelopAdjustments / copyEditSettings /
                   pasteEditSettings.
```

## Dial and touch strip support (Stream Deck+)

`AdjustDevelopSettingAction` is the one action that isn't a button: its
manifest entry declares `"Controllers": ["Encoder"]`, so it can only be
assigned to a **dial** on a Stream Deck+, and it uses the SDK's touch-strip
feedback API (`DialAction.setFeedback`/`setFeedbackLayout`) rather than
`setTitle`/`setImage`.

- **Rotate** (`onDialRotate`): the event payload gives a signed `ticks`
  count and a `pressed` flag (was the dial held down while it was turned).
  This plugin computes `delta = ticks * stepSize * (pressed ? 5 : 1)` and
  sends **one** batched `increment`/`decrement` request for that whole
  rotation - not one request per tick, which is what the reference project
  studied for this plugin does (see docs/PROTOCOL.md). Holding the dial
  down while turning it applies a 5x coarser step, entirely from the SDK's
  own `pressed` flag - no extra UI or settings needed for that.
- **Push** (`onDialDown`): recenters a cosmetic 0-100 "indicator" position
  shown on the touch strip. This is purely a UI reset for this plugin's own
  display - Lightroom's own value is completely untouched, since there is
  no "reset this one parameter" command in its API (only
  `resetAllDevelopAdjustments`, which resets every Develop setting at
  once - see the `develop-utility` action).
- **Touch strip content**: uses Stream Deck's built-in `$B1` layout (a
  title + a value + a bar indicator). The value/indicator do **not**
  reflect Lightroom's actual current setting - there's no API to read that
  back - they show the parameter name and the delta just sent, plus that
  cosmetic indicator position. This is disclosed directly in the action's
  property inspector, not just in this doc.

`src/plugin.ts` is the composition root: it constructs one
`LightroomConnection`, one `PresetManager`, one `PresetApplicationService`,
and one `DevelopControlService`, injects them into all six actions, wires
`LightroomConnection`'s "status" events to (a) push a live status update to
whichever property inspector is open and (b) refresh any button titles that
include the connection status, and starts everything.

## Why this split

- **Lightroom communication knows nothing about Stream Deck.**
  `LightroomConnection`, `PresetManager`, and `PresetApplicationService`
  import nothing from `@elgato/streamdeck`. They could be unit-tested or
  reused by a completely different frontend without modification.
- **Actions know nothing about WebSockets or JSON shapes.** `ApplyPresetAction`
  calls `presetApplication.apply(presetId)` and gets back either success or a
  `PresetApplicationError` with a `code` it can map to a short button label -
  it never touches a raw Lightroom response.
- **One shared cache, many buttons.** `PresetManager` is instantiated once
  and shared by both actions, so "Refresh Lightroom Presets" (pressed once)
  immediately benefits every "Apply Lightroom Preset" button without each
  button re-querying Lightroom itself.

## Persistent state on disk

All plugin-owned state lives under
`~/Library/Application Support/com.keelan182.lightroom-presets/` (kept
outside the `.sdPlugin` bundle so a plugin update/reinstall doesn't wipe it):

| File | Contents | Written by |
|---|---|---|
| `presets-cache.json` | Last known `{ id, name }[]` plus a timestamp | `PresetManager.refresh()` |
| `connection-state.json` | The pairing client GUID Lightroom issued | `LightroomConnection` after a successful register |

Per-button assignments (`presetId`, `presetName`, `titleMode`,
`customTitle`) are **not** stored here - they live in each action
instance's own Stream Deck settings, which Stream Deck itself persists per
button/profile/page. This is what gives requirement #9 (independent button
state) for free: it's simply how Stream Deck action settings already work.

Favorites (`favoritePresetIds`) live in the plugin's **global** settings via
`streamDeck.settings.getGlobalSettings/setGlobalSettings` - shared across
every button/profile, since "favorite" is a property of a preset, not of a
particular button.

## Connection lifecycle

`LightroomConnection` runs a 3-second poll loop (`tick()`):

1. Is the Lightroom process running (macOS `pgrep`, read-only, fixed
   argv)? If not: close any socket, status = `not-running`, and don't
   attempt to connect again until the process reappears.
2. If running and not already `connected`/`connecting`, and the backoff
   window has elapsed, attempt a connection: open the socket, send
   `register`, and wait (up to 12s, since a pairing dialog may be involved).
3. Successful register -> `connected`, backoff resets to 1s.
4. Socket refused/closed -> `disconnected`, backoff doubles up to a 30s cap.
5. Socket opened but `register` never answered -> `unresponsive` (most
   likely an unanswered pairing dialog), backoff doubles.

A connection is opened once and reused for every request; buttons never
open a new socket per key press (requirement #8/#21).

## Macos-only, no automation, no native binaries

- The only OS-level integration is a single, fixed, non-shell,
  argv-array `pgrep -f "Adobe Lightroom"` call used purely to distinguish
  "Lightroom isn't open" from "Lightroom is open but unreachable" for
  clearer messages - never to control Lightroom itself.
- No Accessibility permissions, no UI scripting, no keystroke/mouse
  simulation anywhere in this codebase. All communication goes through
  Lightroom's own WebSocket API.
- No native Node addons are used (the WebSocket client is the pure-JS `ws`
  package; the icon generator is a from-scratch pure-JS PNG encoder), so
  there is nothing that needs separate Intel/Apple Silicon builds - Stream
  Deck's bundled Node.js runtime is already native per-architecture, and
  this plugin's JS runs unmodified on either.

## Known limitation: no folder hierarchy

See docs/PROTOCOL.md for the full explanation - Lightroom's External
Controller API does not return folder/group metadata for presets, so the
"Presets > User Presets > Concert Warm" nested structure requested in the
spec is not something this plugin can build from real data without
inventing it. Favorites (an actual plugin-side grouping we do control) are
implemented instead.
