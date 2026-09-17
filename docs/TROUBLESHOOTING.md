# Troubleshooting

## First: read the plugin's log file

Every important event (startup, connection status changes, preset
discovery, preset application, errors, reconnection attempts) is logged to:

```
~/Library/Application Support/com.elgato.StreamDeck/Plugins/com.keelan182.lightroom-presets.sdPlugin/logs/com.keelan182.lightroom-presets.0.log
```

(Numbered log files rotate; check the highest number for the most recent
run.) Set `"Nodejs": { "Debug": "enabled" }` is already on in
`manifest.json`, which raises the log level and also mirrors logs to the
console when launched via `streamdeck dev`/`npm run watch`. No photo
content or catalog metadata is ever logged - only preset ids/names, connection
state, and error text.

## "Button shows ⚠ / Not Connected"

This means `LightroomConnection`'s status was `disconnected`: Lightroom's
process was found running, but the WebSocket connection to
`ws://127.0.0.1:7682` was refused or dropped. Almost always this means:

1. Open Lightroom Desktop/CC.
2. Go to **Preferences > Interface**.
3. Enable **"Enable external controllers"** (the exact wording may vary
   slightly by Lightroom version - look for "external controller(s)").
4. Restart Lightroom if the toggle was previously off - some versions only
   start the local server on next launch.

## "Button shows No Lightroom"

`LightroomConnection`'s status was `not-running` - the plugin could not
find a running `Adobe Lightroom` process via `pgrep`. Open Lightroom
Desktop/CC and the button should recover within ~3 seconds (the poll
interval) without needing to restart Stream Deck or the plugin.

If Lightroom **is** open and you still see this, the process-name pattern
this plugin checks for (`"Adobe Lightroom"`, see
`src/lightroom/connection.ts`, `LIGHTROOM_PROCESS_PATTERN`) may not match
the exact process name on your macOS version - this was written from
publicly documented conventions, not confirmed against a live Lightroom
Desktop install, since this repository was built in a Linux environment
without access to a licensed copy of Lightroom or a physical Mac. Run
`ps aux | grep -i lightroom` in Terminal while Lightroom is open, note the
real process name, and update `LIGHTROOM_PROCESS_PATTERN` to match (then
`npm run build`).

## "Button shows No Response / Wait"

Status was `unresponsive`: the socket opened, but Lightroom never answered
the `register` handshake within 12 seconds. The most common cause is an
unanswered **pairing dialog** in Lightroom - switch to Lightroom and look
for a prompt asking to allow "Stream Deck Lightroom Presets" to connect,
then click **Allow**. If you don't see one, quit and reopen Lightroom (this
resets its External Controller server) and try again.

## "Preset not found: <name>"

The preset id saved on that button no longer exists in Lightroom's own
preset list - most likely it was renamed or deleted since you assigned it.
Fix it in one of two ways:

- Open that button's settings in Stream Deck and pick the (renamed/new)
  preset from the dropdown again.
- Press **Refresh Lightroom Presets** first - this re-syncs the cache and
  will flag (via a yellow alert + title change) any other buttons pointing
  at presets that no longer exist, so you can catch several at once.

## "No presets in the dropdown" / property inspector shows nothing

The plugin hasn't successfully fetched a preset list yet. Make sure
Lightroom is open with external controllers enabled (see above), then
either press the **Refresh Lightroom Presets** button on your Stream Deck,
or click **Refresh Presets** inside the property inspector of an "Apply
Lightroom Preset" action. The plugin also auto-refreshes once, automatically,
the first time it detects a successful connection each session.

## Presets list looks stale after renaming/adding presets in Lightroom

Preset discovery is on-demand by design (see docs/ARCHITECTURE.md /
requirement to avoid constant polling) - it runs once at startup from the
disk cache, once automatically right after connecting, and otherwise only
when you press **Refresh Lightroom Presets**. Press it after making preset
changes in Lightroom.

## The Stream Deck app shows the plugin but actions don't do anything

1. Check the log file above for a stack trace.
2. Confirm `com.keelan182.lightroom-presets.sdPlugin/bin/plugin.js` exists
   (run `npm run build` if you cloned the repo and it's missing - the repo
   ships a prebuilt copy, but a fresh `git clone` of just the source without
   the build step obviously won't have run it).
3. Quit and relaunch the Stream Deck app after installing/updating the
   plugin.

## This plugin cannot detect "no photo selected" precisely

Lightroom's `applyPreset` command does not return a distinct, documented
error for "no photo is currently selected" (see docs/PROTOCOL.md) - the
External Controller API's error reporting for this command was not
something we could fully characterize without live access to Lightroom.
When `applyPreset` fails for any reason other than the ones this plugin can
positively identify (not running / not connected / unresponsive / unknown
preset id), the button will show a generic "LR Error" and the log will
contain whatever raw response or timeout Lightroom actually returned -
check the log for specifics if this happens consistently.

## Verifying this yourself

This project was built and validated in a Linux sandbox without a licensed
Lightroom Desktop/CC install, a physical Mac, or Stream Deck hardware
available to the assistant that wrote it. Everything that could be
verified without those things was: the manifest passes Elgato's own
`@elgato/cli validate`, the TypeScript compiles under `strict` mode, the
bundle produced by `npm run build` is valid JavaScript and starts up
without throwing (up to the point where it needs the Stream Deck app's own
launch arguments), and the wire protocol matches what a real third-party
Lightroom Loupedeck plugin implements. What has **not** been verified is an
actual physical button press causing an actual preset to apply inside a
running Lightroom Desktop/CC on real hardware - that is the one test only
you can run, on your Mac. See docs/TESTING.md for exactly how, and please
report back anything in this document that doesn't match what you observe
(especially the `pgrep` process-name pattern above) so it can be corrected.
