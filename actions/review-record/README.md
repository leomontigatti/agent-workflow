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
      - uses: leomontigatti/agent-workflow/actions/review-record@<commit sha> # v1.0.0
```

Pin the action to the commit of a release tag, with the tag as the comment: zizmor checks that
the comment's ref still points at the pinned commit, and a branch such as `main` stops doing so
on the next merge, failing every PR of the project. A change to the review rules reaches the
project when it bumps the pin (Dependabot's `github-actions` ecosystem proposes each new tag).
The repo is public so that public projects can call it.

Make `review-record` a required context of the default branch's protection once the project's
`docs/agents/review.md` has its `review-paths` block. The rules are in
[`review.py`](../../skills/implement/scripts/review.py).
