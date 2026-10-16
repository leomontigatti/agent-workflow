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
      - uses: leomontigatti/agent-workflow/actions/review-record@<commit sha> # main
```

Pin the action to a commit, as a workflow linter such as zizmor asks; a change to the review
rules then reaches the project when it bumps the pin (Dependabot's `github-actions` ecosystem
does it). The repo is public so that public projects can call it.

Make `review-record` a required context of the default branch's protection once the project's
`docs/agents/review.md` has its `review-paths` block. The rules are in
[`review.py`](../../skills/implement/scripts/review.py).
