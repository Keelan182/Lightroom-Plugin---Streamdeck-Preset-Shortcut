# Test plan

This plugin was built and typechecked/bundled/validated in a Linux sandbox
with no access to macOS, a physical Stream Deck, or a licensed Lightroom
Desktop/CC install. Everything in this document beyond "Build-time checks"
needs to be run by you, on your Mac, with your Stream Deck and your
Lightroom Desktop/CC. Treat every unchecked item as **not yet verified**,
not as "assumed working."

## Build-time checks (already done, repeatable via `npm run build`)

- [x] `npx tsc --noEmit` passes under `strict` mode.
- [x] `npx rollup -c` produces a valid, syntactically-correct bundle.
- [x] `npx @elgato/cli validate com.keelan182.lightroom-presets.sdPlugin`
      passes Elgato's own manifest schema validation.
- [x] `npx @elgato/cli pack` produces an installable `.streamDeckPlugin`.
- [x] Generated icons render correctly (verified visually during
      development).
- [x] Running the bundle standalone fails only on the expected
      "missing Stream Deck launch arguments" error - i.e. the plugin's own
      startup code (settings load, connection manager construction, action
      registration) runs without throwing.

## Critical acceptance test (do this first)

1. Install the plugin: double-click
   `com.keelan182.lightroom-presets.streamDeckPlugin` (see README.md).
2. Open Lightroom Desktop/CC; enable Preferences > Interface > "Enable
   external controllers" if you haven't already, and restart Lightroom.
3. Open a photo in the Library or an album.
4. Open the Stream Deck app, add "Apply Lightroom Preset" to a button.
5. In its property inspector, confirm the preset dropdown populates with
   your real presets (click "Refresh Presets" if it's empty).
6. Select an actual preset you can visually recognize the effect of.
7. Press the physical button.
8. **Verify Lightroom visibly re-renders the photo with that preset's
   look**, and the button briefly shows a green checkmark.

If step 8 doesn't happen, check docs/TROUBLESHOOTING.md and the plugin log
before assuming the architecture is wrong - most likely causes are the
external-controllers setting, an unanswered pairing dialog, or a
process-name mismatch in the `pgrep` check.

## Develop controls (new actions, added after the initial preset plugin)

None of this was testable without physical Stream Deck+ hardware and a
live Lightroom session - treat all of it as unverified until you've run it.

- [ ] **Adjust Develop Setting**: assign to a Stream Deck+ dial, pick
      "Exposure", open a photo, turn the dial one click clockwise ->
      Lightroom's exposure should visibly increase by the configured step.
      Turn counter-clockwise -> decreases.
- [ ] Hold the dial down while turning it -> the change should be
      noticeably bigger (5x) than turning it unheld.
- [ ] Press the dial without turning it -> only the touch strip's bar
      indicator should recenter; re-open the photo's Develop panel in
      Lightroom and confirm the actual exposure value is unchanged.
- [ ] Try a few other parameters (Temperature, Tint, Clarity) and confirm
      each maps to the right Lightroom control, not a different one -
      this is the one place a wrong parameter-name string would be
      silently wrong rather than erroring.
- [ ] Assigning "Adjust Develop Setting" to a regular button (not a dial)
      on a non-Stream Deck+ device - confirm it's simply not offered as
      droppable there (Encoder-only manifest declaration), rather than
      behaving oddly.
- [ ] **Toggle Lens Correction**: press once with "Lens Profile
      Corrections" selected -> Lightroom's lens corrections checkbox
      should toggle. Press again -> toggles back. Then change the same
      checkbox directly inside Lightroom and press the Stream Deck button -
      confirm (and note) that the button's ON/OFF state was already stale
      before you pressed it, per the documented limitation.
- [ ] **Flag & Rate Photo**: try a flag, a star rating, and a color label
      on a selected photo; confirm each lands on the correct photo and the
      correct value (e.g. "Rating: 3 stars" doesn't set 4).
- [ ] **Develop Utility**: "Reset All Develop Adjustments" on a photo with
      several edits - confirm every adjustment resets, not just one.
      "Copy Edit Settings" on one photo then "Paste Edit Settings" on
      another - confirm the second photo's edits now match the first.

## Connection

- [ ] Lightroom closed when Stream Deck/plugin starts -> button shows "No
      Lightroom"; pressing it shows an alert, doesn't crash.
- [ ] Open Lightroom while the plugin is running -> status recovers to
      Connected within a few seconds without restarting anything.
- [ ] Lightroom opens *after* Stream Deck/this plugin -> same recovery.
- [ ] Quit Lightroom while connected -> status falls back to "No
      Lightroom"; no repeated connection-refused error spam in the log
      (backoff should be visibly increasing, capped at 30s).
- [ ] Restart Lightroom (quit + reopen) -> plugin reconnects and
      re-registers; check whether a new pairing dialog appears (expected
      the first time; the persisted client GUID is intended to avoid this
      on subsequent restarts, but this specific behavior is unverified -
      see docs/PROTOCOL.md).
- [ ] Toggle "Enable external controllers" off while connected -> next
      reconnect attempt should show "Not Connected", not "No Lightroom".

## Presets

- [ ] A catalog with a single preset -> discovery + apply works.
- [ ] A catalog with 100+ presets -> "Refresh Lightroom Presets" completes
      in a reasonable time (this plugin batches name lookups 4-at-a-time;
      note how long it actually takes and compare against
      `NAME_FETCH_CONCURRENCY`/`NAME_FETCH_STAGGER_MS` in
      `src/lightroom/presetManager.ts` if it feels slow).
- [ ] Preset names containing spaces and special characters (emoji,
      accents, `&`, quotes) display correctly in the dropdown and on the
      button title.
- [ ] Two presets that happen to share the same name (different ids) -
      confirm the dropdown still lets you pick the correct one (it's keyed
      by id, but visually indistinguishable names are a real edge case
      worth eyeballing).
- [ ] Presets organized into folders/groups in Lightroom's own UI - confirm
      (per docs/PROTOCOL.md) that this plugin's list is flat and does not
      reflect that folder structure; this is a known, documented API
      limitation, not a bug to fix.
- [ ] Delete a preset that's assigned to a button, then press "Refresh
      Lightroom Presets" -> that button should flip to an alert state
      titled "Preset not found: <old name>".
- [ ] Rename a preset that's assigned to a button, then refresh -> since
      the id is unchanged, the button should just pick up the new name
      automatically (this is the entire point of storing the id rather
      than trusting the name).

## Stream Deck

- [ ] Multiple "Apply Lightroom Preset" buttons on the same page, each with
      a different preset - confirm changing one button's assignment never
      affects another's title or behavior.
- [ ] The same preset assigned to two different buttons - both apply it
      correctly.
- [ ] Buttons spread across multiple pages/profiles - confirm titles stay
      correct when you navigate away and back (`onWillAppear` re-renders
      the title every time).
- [ ] Changing a button's preset in the property inspector immediately
      updates its title without needing to press the button.
- [ ] Stream Deck app restart - buttons should show their last-known preset
      names immediately from the on-disk cache, even before Lightroom
      reconnects.

## Lightroom content

- [ ] Apply a preset to a RAW photo.
- [ ] Apply a preset to a JPEG.
- [ ] Apply with a photo selected vs. nothing selected - as documented in
      docs/PROTOCOL.md and docs/TROUBLESHOOTING.md, this plugin cannot
      currently distinguish "no photo selected" from other generic
      failures; note in your test results exactly what happens (error
      text, log contents) so this can be tightened up if Lightroom does
      return something identifiable.

## macOS

- [ ] Apple Silicon Mac - since this is a Node.js plugin with no native
      addons, it should run unmodified via Stream Deck's own bundled
      Node.js runtime; confirm there's no Rosetta warning.
- [ ] Restart the plugin (Stream Deck > right-click > "Restart Plugin" or
      equivalent) - reconnects cleanly.
- [ ] Restart the Stream Deck app - plugin relaunches and reconnects.
- [ ] Reboot macOS - Lightroom and Stream Deck both cold-starting; confirm
      the plugin eventually reaches Connected without manual intervention
      once both apps are open.

## Reporting results

Since none of the sections above were run by the assistant that built this,
please note in your own copy of this file (or an issue/PR comment) which
items passed, which failed, and the exact log lines for any failure -
particularly anything under "Connection" and "Lightroom content", since
those depend on real Lightroom behavior this project could only infer from
third-party documentation.
