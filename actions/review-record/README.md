# review-record action

A project's CI calls it on every pull request, after checking out the project with its full
history:

```yaml
name: review-record
on:
  pull_request:
    types: [opened, edited, synchronize, reopened]
permissions:
  contents: read
  pull-requests: read
jobs:
  review-record:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: leomontigatti/agent-workflow/actions/review-record@<commit sha> # v1.0.0
```

The action reads the PR body when it runs, so `gh run rerun` checks the record as it is now:
rerun a red run after fixing the record instead of pushing an empty commit. A private repository
needs `pull-requests: read` for that read; a public one reads it with `contents: read` alone.

The `edited` event fires on every body edit, and a project's other `edited` checks restart with
it and block the merge until they finish. A check that reads only the title, such as `pr-title`,
skips the body edits with `if: github.event.action != 'edited' || github.event.changes.title`: a
skipped job still satisfies a required check.

Pin the action to the commit of a release tag, with the tag as the comment: zizmor checks that
the comment's ref still points at the pinned commit, and a branch such as `main` stops doing so
on the next merge, failing every PR of the project. A change to the review rules reaches the
project when it bumps the pin (Dependabot's `github-actions` ecosystem proposes each new tag).
The repo is public so that public projects can call it.

Make `review-record` a required context of the default branch's protection once the project's
`docs/agents/review.md` has its `review-paths` block. The rules are in
[`review.py`](../../skills/implement/scripts/review.py).
