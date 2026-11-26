# UI Prototype

Generate **structurally different UI variations** on the real route, switchable from a floating bottom bar. The user drives them in a live preview, picks one (or steals bits from each), and the winner becomes the spec the implementation follows.

If the question is about logic/state rather than what something looks like, this is the wrong branch. Use [LOGIC.md](LOGIC.md).

## When this is the right shape

- "What should this page look like?"
- "I want to see a few options for this dashboard before committing."
- "Try a different layout for the settings screen."
- The `implement` skill's step 1 sends a change here before any code: a new screen or flow, or a change to a screen's layout or interaction.
- Any time the user would otherwise spend a day picking between three vague mockups in their head.

## Two sub-shapes: strongly prefer sub-shape A

A UI prototype is much easier to judge when it's **butting up against the rest of the app**: real header, real sidebar, real data, real density. A throwaway route on its own is a vacuum: every variant looks fine in isolation. Default to sub-shape A whenever there's a plausible existing page to host the variants. Only reach for sub-shape B if the prototype genuinely has no nearby home.

### Sub-shape A: adjustment to existing pages (preferred)

The routes already exist. Variants are rendered **on the same routes**, gated by a `?variant=` URL search param. The existing data fetching, params, and auth all stay. Only the rendering swaps. This is the default; pick it unless there's a specific reason not to.

If the prototype is for something that doesn't yet have a page but _would naturally live inside one_ (a new section of the dashboard, a new card on the settings screen, a new step in an existing flow), it's still sub-shape A. Mount the variants inside the host page.

When the question is the path between screens (where an action starts, where the user lands), the variants **span routes**: mount the switcher on every route involved, keep `?variant=` on every link between them, and carry any throwaway draft in the URL's search params so a reload or a variant switch keeps it.

### Sub-shape B: a new page (last resort)

Only use this when the thing being prototyped genuinely has no existing page to live inside (e.g. an entirely new top-level surface, or a flow that can't be embedded anywhere sensible).

Create a **throwaway route** following whatever routing convention the project already uses. Don't invent a new top-level structure. Name it so it's obviously a prototype (e.g. include the word `prototype` in the path or filename). Same `?variant=` pattern.

Before committing to sub-shape B, sanity-check: is there really no existing page this could be embedded in? An empty route hides design problems that a populated one would expose.

In both sub-shapes the floating bottom bar is identical.

## Process

### 1. State the question and pick N

The count follows the change: **3 variants** for a new screen or flow, **1** for a change to an existing screen, and **2** when that change holds a real layout or interaction choice. Cap at 5: past that they stop being radically different and start being noise.

Write down the plan in one line, in the prototype's location or a top-of-file comment:

> "Two variants of where the sandbox opens from the rules form, switchable via `?variant=`, on `/rules` and `/sandbox`."

### 2. Generate structurally different variants

Draft each variant. Hold each one to:

- The page's purpose and the data it has access to.
- **Patterns a screen already uses**: the components, layouts and tokens the app's screens show today, by the project's style guide. A component that exists in the repo but on no screen (a drawer nobody opens) is a new pattern too. Mark every new pattern on screen with a visible "new" badge, so the user judges it knowingly.
- A clear exported component name, e.g. `VariantA`, `VariantB`, `VariantC`.

Variants must be **structurally different**: different layout, different information hierarchy, different primary affordance, not just different colours. Three slightly-tweaked card grids isn't a UI prototype, it's wallpaper. If two drafts come out too similar, redo one with explicit "do not use a card grid" guidance. A lone variant (a change with no real choice) is the proposed design itself.

Keep throwaway state alive across the variant's own UI: when a panel, dialog or tab unmounts its content on close, hold the state above it, so the user's conversation or draft survives closing and reopening.

### 3. Wire them together

Create a single switcher component on the route:

```tsx
// pseudo-code, adapt to the project's framework
const variant = searchParams.get("variant") ?? "A";
return (
  <>
    {variant === "A" && <VariantA {...data} />}
    {variant === "B" && <VariantB {...data} />}
    {variant === "C" && <VariantC {...data} />}
    <PrototypeSwitcher variants={["A", "B", "C"]} current={variant} />
  </>
);
```

For sub-shape A (existing page): keep all the existing data fetching above the switcher; only the rendered subtree changes per variant.

For sub-shape B (new page): the throwaway route under `/prototype/<name>` mounts the same switcher.

### 4. Build the floating switcher

A small fixed-position bar at the bottom-centre of the screen with three pieces:

- **Left arrow**: cycles to the previous variant (wraps around).
- **Variant label**: shows the current variant key and, if the variant exports a name, that name too. e.g. `B (Sidebar layout)`.
- **Right arrow**: cycles forward (wraps around).

Behaviour:

- Clicking an arrow updates the URL search param (use the framework's router, e.g. `router.replace` on Next, `navigate` on React Router, etc) so the variant is shareable and reload-stable.
- Keyboard: `←` and `→` arrow keys also cycle. Don't intercept arrow keys when an `<input>`, `<textarea>`, or `[contenteditable]` is focused.
- Visually distinct from the page (e.g. high-contrast pill, subtle shadow) so it's obviously not part of the design being evaluated, built from the project's own button and colour tokens so it passes the lint.
- Hidden in production builds: gate on `process.env.NODE_ENV !== 'production'` or an equivalent check, so a stray prototype merge can't ship the bar to users.

Put the switcher in a single shared component so both sub-shapes can reuse it. Locate it wherever shared UI lives in the project.

### 5. Check it yourself

Launch by `docs/agents/verification.md` § Launch, once, as a background command, then poll the URL it gives until it answers; a second launch collides with the first. Drive every variant with the browser CLI § Drive names, or with the machine's browser as the `implement` skill's [PREVIEW.md](../implement/PREVIEW.md) says when it names none: each renders with the seed data, the switcher works by button and by key, and the console is clean. On a paired device the user drives them, as [PREVIEW.md](../implement/PREVIEW.md) says. Fix what breaks first. Done when every variant passes: the user reviews designs, never a broken page.

### 6. Hand it over

Expose the route's port as a preview and give the user its address; on a paired device, give the local address and expose nothing, as [PREVIEW.md](../implement/PREVIEW.md) says. Tell the user the `?variant=` keys, and one line per variant saying what it bets on. The user drives the page and comments in the thread. Each ask changes the **prototype**, then step 5 runs again. Done when the user names a winner.

### 7. Capture the answer and clean up

Capture the winner the way the [SKILL](SKILL.md) describes, and stop what step 5 launched by `docs/agents/verification.md` § Cleanup, closing the preview tab and any browser CLI session. The implementation then follows the winner:

- **Sub-shape A**: the winner's markup moves into the existing pages; the losing variants and the switcher stay on the prototype branch.
- **Sub-shape B**: the winning variant becomes a real route; the throwaway route and the switcher stay on the prototype branch.

The full set of variants is the primary source, so it lives on the prototype branch, never in main, since variant components and the switcher left in the main branch rot fast and confuse the next reader.

## Anti-patterns

- **Variants that differ only in colour or copy.** That's a tweak, not a prototype. Real variants disagree about structure.
- **Sharing too much code between variants.** A shared `<Header>` is fine; a shared `<Layout>` defeats the point. Each variant should be free to throw out the layout.
- **Wiring variants to real mutations.** Read-only prototypes are fine. If a variant needs to mutate, point it at a stub: the question is "what should this look like", not "does the backend work".
- **Promoting the stubs.** The implementation copies the winner's markup and layout, and rewrites its data, mutations and behaviour test-first: the stubs were written to look right, never to be right.
