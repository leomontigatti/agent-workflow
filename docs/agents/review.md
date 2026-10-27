# Review: agent-workflow

## Hotspots

Where this repo gets hurt, for the correctness brief:

- a script that reads or rewrites a tracked structured file (`upstreams/sources.json`, a skill's
  frontmatter, a state file): keys in another order, non-ASCII text, the encoding on both the read
  and the write, a value the file lacks, and a write that dies halfway and leaves the file empty or
  partial.
