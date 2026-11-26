# Driving a page with the platform's browser

The browser CLI that `docs/agents/verification.md` § Drive names does the clicking and takes the
evidence. This file is for a project whose § Drive names none, which drives with the browser on
the thread's machine. A project's § Launch says what to start and § Feature map which flows to
drive; this file says how to drive them.

**A real click or none.** A click made by running script in the page (`element.click()`, a
dispatched event, a `fetch`) skips what stops a user, such as a covered button or a dialog in the
way, so it proves nothing about the path. When the browser cannot make a click, report the path
as not clicked.

**On a paired device** a port gets no preview address and this browser cannot reach the device's
pages. Give the user the local address (`http://localhost:<port>`) and the flow to drive, and ask
for a screenshot of each state a capture needs: that screenshot is the evidence.

## The loop

1. **Launch** what § Launch names and open the app in the browser. A page the user should see
   too is a port exposed as a preview: its address is open to anyone who has it while the
   machine is awake, so expose only an app running on test data.
2. **Size** the window to the viewport the screen is designed for, once, and read the width the
   page laid out at (`innerWidth`) before each capture. Check a dense screen (a table, a long
   row) at the narrower width the project names too.
3. **Capture the reference** (`implement` step 1): the before, before the first edit, or the
   approved variant from its prototype branch.
4. **Drive** the flow by real clicks and typing, targeting an element by what names exactly one
   (its label, its role and name, an id). Before every capture or assertion, wait for the text
   or address the step should produce, one only the main content shows: a navigation label
   matches before the page loads.
5. **Diagnose from the page**: its console errors and its state (a text, a value, the address).
   Done when the touched screens show no error.
6. **Capture the after**, same screen, data, account, size and tool as the reference. A change
   to motion or interaction is a recording instead.
7. **Stop** what § Launch started (§ Cleanup), previews included.

Note every place the browser fell short in the final report.
