# review-record action

A project's CI calls it on every pull request, after checking out the project with its full
history:

```yaml
name: review-record
on:
  pull_request:
    types: [opened, edited, synchronize, reopened]
jobs:
  review-record:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: leomontigatti/agent-workflow/actions/review-record@main
```

Make `review-record` a required context of the default branch's protection once the project's
`docs/agents/review.md` has its `review-paths` block. The rules are in
[`review.py`](../../skills/implement/scripts/review.py).
