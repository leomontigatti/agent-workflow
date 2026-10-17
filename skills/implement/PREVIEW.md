# Driving a page with T3's preview tools

In a T3 thread, `implement` step 4 drives what a user sees with T3's own browser, the preview
tools, rather than a browser CLI the project installs. A project's `docs/agents/verification.md`
§ Launch says what to start and § Feature map which flows to drive; this file says how to drive
them. Outside T3 (no preview tools), § Drive's fallback applies.

The preview tools are on trial (`preview-tools-verification` in the shared
`t3-dependencies.md`). Note every place they fall short in the final report, so the trial has
its numbers.

When `preview_open` is refused, the machine is not set up for them: "Agent browser access" is off
in T3's Settings, or the host blocks the browser's sandbox (the error names
`sudo ~/.t3/bin/t3 browser setup`). Both are the user's to fix. Finish with § Drive's fallback,
and open the final report with the refusal's exact text.

## The loop

1. **Open** a tab on the launched app: `preview_open` with the URL, and `open: false` unless the
   user should watch. Keep the returned `tabId` and pass it on every call; parallel subagents
   each open their own tab (`reuseExistingTab: false`).
2. **Size** the viewport the screen is designed for with `preview_resize`, once: it holds across
   navigations and sign-ins. Check a dense screen (a table, a long row) at the narrower width the
   project names too.
3. **Capture the before**, before the first edit: `preview_snapshot` with `save: true`, its
   `screenshotPath` the evidence file, or the browser CLI when `docs/agents/verification.md`
   § Evidence names it. The preview saves every capture at most 1280 px wide, scaling a wider
   viewport down, and at any viewport wider than 640 px draws a blurred backdrop (behind a
   dialog or sheet) as mirrored tiles of the page: a capture artifact, not an app bug.
4. **Drive** the flow with `preview_click`, `preview_type`, `preview_select`, `preview_press` and
   `preview_navigate`, targeting elements by the `aria-ref` refs of the latest `preview_snapshot`.
   Refresh the snapshot after a navigation. Before every capture or assertion, `preview_wait_for`
   the text, locator or URL the step should produce, one only the main content shows (a
   navigation label matches before the page loads). Click a menu item by a ref from a snapshot
   taken while the menu is open, or by a role locator: the snapshot's tree stops at 10 000
   characters, so a long page leaves a popover without refs. A menu that closed in between fails
   as a bare click timeout: reopen it and click again.
5. **Diagnose from the page**: the snapshot's diagnostics for console errors, `preview_evaluate`
   for anything the snapshot omits. Its console entries cover the tab's whole life: read their
   timestamps to tell which screen logged what. Done when the touched screens show no error.
6. **Capture the after**, same screen, data, account, size and tool as the before. A change to motion or interaction is a recording instead:
   `preview_recording_start` before the interaction, `preview_recording_stop` after.
7. **Close** the tab with `t3_preview_close`, then stop what § Launch started (§ Cleanup).

Show the user a capture by embedding its path in the reply. Attach the before and after to the
PR as `docs/agents/verification.md` § Evidence says, from the tool it names: upload the files,
never link a `screenshotPath`, since T3 deletes saved captures after the days set in Settings →
Storage.
