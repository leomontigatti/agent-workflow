# GLOSSARY.md Format

## Structure

```md
# <Project>

{One or two sentences on what the glossary covers.}

## Ordering

**`order`** — ui: "Pedido"
{A one or two sentence description of the term.}
_Avoid_: purchase, transaction

**`invoice`** — ui: "Factura"
A request for payment sent to a customer after delivery.
_Avoid_: bill, payment request

**`cliente`** _(retired term)_ — no code identifier
{Why it was retired, and the term that replaced it.}
```

Each heading is the canonical identifier, the name to use in code. When a user reads the product
in another language than the code's, follow it with `ui:` and the term the user sees. How prose
borrows those terms is in the code-language rules `AGENTS.md` routes to.

## Rules

- **Be opinionated.** When multiple words exist for the same concept, pick the best one and list the others under `_Avoid_`.
- **Keep definitions tight.** One or two sentences max. Define what it IS, not what it does.
- **Only include terms specific to this project's context.** General programming concepts (timeouts, error types, utility patterns) don't belong even if the project uses them extensively. Before adding a term, ask: is this a concept unique to this context, or a general programming concept? Only the former belongs.
- **Group terms under subheadings** when natural clusters emerge. If all terms belong to a single cohesive area, a flat list is fine.
