# Driving a page with T3's preview tools

In a T3 thread, `implement` step 4 drives what a user sees with T3's own browser, the preview
tools, rather than a browser CLI the project installs. A project's `docs/agents/verification.md`
§ Launch says what to start and § Feature map which flows to drive; this file says how to drive
them. Outside T3 (no preview tools), § Drive's fallback applies.

The preview tools are on trial (`preview-tools-verification` in the shared
`t3-dependencies.md`). Note every place they fall short in the final report, so the trial has
its numbers.

## The loop

1. **Open** a tab on the launched app: `preview_open` with the URL, and `open: false` unless the
   user should watch. Keep the returned `tabId` and pass it on every call; parallel subagents
   each open their own tab (`reuseExistingTab: false`).
2. **Size** the viewport the screen is designed for with `preview_resize`, and check a dense
   screen (a table, a long row) at the narrower width the project names too.
3. **Capture the before**, before the first edit: `preview_snapshot` with `save: true`. Its
   `screenshotPath` is the evidence file.
4. **Drive** the flow with `preview_click`, `preview_type`, `preview_select`, `preview_press` and
   `preview_navigate`, targeting elements by the `aria-ref` refs of the latest `preview_snapshot`.
   Refresh the snapshot after a navigation. Before every capture or assertion, `preview_wait_for`
   the text, locator or URL the step should produce, so nothing is captured mid-transition.
5. **Diagnose from the page**: the snapshot's diagnostics for console errors, `preview_evaluate`
   for anything the snapshot omits. Done when the touched screens show no error.
6. **Capture the after**, same screen, data, account and size: `preview_snapshot` with
   `save: true`. A change to motion or interaction is a recording instead:
   `preview_recording_start` before the interaction, `preview_recording_stop` after.
7. **Close** the tab with `t3_preview_close`, then stop what § Launch started (§ Cleanup).

Show the user a capture by embedding its `screenshotPath` in the reply. Attach the before and
after to the PR as `docs/agents/verification.md` § Evidence says.
