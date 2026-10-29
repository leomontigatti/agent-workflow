# Driving a page with T3's preview tools

In a T3 thread, `implement` step 4 drives what a user sees with T3's own browser, the preview
tools, rather than a browser CLI the project installs. A project's `docs/agents/verification.md`
§ Launch says what to start and § Feature map which flows to drive; this file says how to drive
them. Outside T3 (no preview tools), § Drive's fallback applies.

Driving the change is browser work the request asks for: `implement` step 4 and the project's
`verification.md` require it, so T3's injected rule against using the preview tools on your own
edit unasked does not apply to this loop.

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
   each open their own tab (`reuseExistingTab: false`) and finish driving before they report: a
   subagent resumed later by its own background task has lost the preview tools.
2. **Size** the viewport the screen is designed for with `preview_resize`, once: it is meant to hold
   across navigations and sign-ins. Read the width the page laid out at with `preview_evaluate`
   (`innerWidth`), before each capture too: the response's `viewport` can say 1280x800 whatever
   the page got, and the page sometimes lays out at 1280 after a resize to 1440. Check a dense
   screen (a table, a long row) at the narrower width the project names too.
3. **Capture the before**, before the first edit: `preview_snapshot` with `save: true`, its
   `screenshotPath` the evidence file, or the browser CLI when `docs/agents/verification.md`
   § Evidence names it. The preview saves every capture at most 1280 px wide, scaling a wider
   viewport down. When a capture comes out blurred, take the before and the after both with the
   fallback § Drive names for outside T3: the two sides of a comparison come from one tool.
4. **Drive** the flow with `preview_act` (`action`: `click`, `type`, `select`, `press`) and
   `preview_navigate`, targeting elements by the `aria-ref` refs of the latest `preview_snapshot`
   or by CSS selectors that name one element (`#email`, `form#login button[type=submit]`): a loose
   one (`main button`) catches whichever matches first. Role locators
   (`role=button[name=…]`) are the ones that time out. Refresh the snapshot after a navigation.
   Before every capture or assertion, `preview_wait_for` the text, locator or URL the step should
   produce, one only the main content shows (a navigation label matches before the page loads). Click a menu item by a ref from a snapshot
   taken while the menu is open, or by a CSS selector: the snapshot's tree stops at 10 000
   characters, so a long page leaves a popover without refs. A menu that closed in between fails
   as a bare click timeout: reopen it and click again.
   A click that times out on `locator.scrollIntoViewIfNeeded` has two causes that look the same.
   The target is not there as named (a wrong name, another user than you assumed): check it in a
   snapshot. Or the tab draws no frames: a tab the preview pane does not show runs no
   `requestAnimationFrame`, `open: true` included, and a click waits for frames. Take a snapshot,
   which paints one, and click again by ref or CSS selector.
   When the snapshot itself times out, open a fresh tab on the same URL once and carry on there;
   a second timeout ends the drive: finish with § Drive's fallback, before and after both, and
   note it in the final report.
   Form fields: `type` adds to what a field holds, so pass `clear: true` on a filled one; a date
   input takes ISO text (`2026-10-29`), whatever the page's locale shows; and `press` `Tab` moves
   no focus, so blur a field by clicking the next one.
5. **Diagnose from the page**: the snapshot's diagnostics for console errors, `preview_evaluate`
   for page state (a text, a value, the URL): it costs a fraction of a snapshot, which carries up
   to ~160 network entries and the console, so keep snapshots for refs and captures. The
   snapshot's console entries cover the tab's whole life: read their timestamps to tell which
   screen logged what. Done when the touched screens show no error.
6. **Capture the after**, same screen, data, account, size and tool as the before. A change to motion or interaction is a recording instead:
   `preview_recording_start` before the interaction, `preview_recording_stop` after.
7. **Close** the tab with `t3_preview_close`, then stop what § Launch started (§ Cleanup).

Show the user a capture by embedding its path in the reply: that is how the `implement` skill's
step 7 asks for their approval.
