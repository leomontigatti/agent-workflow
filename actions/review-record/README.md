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
skips the edits that change neither the title nor the base. A skipped job reports a success under
its name, which would turn a red title green, so the skipped run takes another name:

```yaml
concurrency:
  group: pr-title-${{ github.event.pull_request.number }}-${{ github.event.action == 'edited' && github.event.changes.title == null && github.event.changes.base == null && 'skip' || 'check' }}
  cancel-in-progress: true
jobs:
  pr-title:
    name: ${{ github.event.action == 'edited' && github.event.changes.title == null && github.event.changes.base == null && 'pr-title (title unchanged)' || 'pr-title' }}
    if: github.event.action != 'edited' || github.event.changes.title != null || github.event.changes.base != null
```

The required `pr-title` context then keeps the verdict of the last run that read the title. A
workflow with a `concurrency` group splits it the same way, or a body edit right after a push
cancels the run that checks the title.

Pin the action to the commit of a release tag, with the tag as the comment: zizmor checks that
the comment's ref still points at the pinned commit, and a branch such as `main` stops doing so
on the next merge, failing every PR of the project. A change to the review rules reaches the
project when it bumps the pin (Dependabot's `github-actions` ecosystem proposes each new tag).
The repo is public so that public projects can call it.

Make `review-record` a required context of the default branch's protection once the project's
`docs/agents/review.md` has its `review-paths` block. The rules are in
[`review.py`](../../skills/implement/scripts/review.py).
