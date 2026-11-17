#!/usr/bin/env python3
"""Cut a checkout's sources into slices for `lifetime-audit` step 2, highest lifetime score first.

Usage: python3 -I scan.py <checkout> [--under <dir>] [--slice-lines N] [--skip <state file>]

Reads the files git tracks in <checkout>, as checked out: TypeScript and JavaScript sources, tests,
seeds and generated files left out, under <dir> when given. It judges nothing and filters nothing:
every file lands in one slice, and the score only orders the slices and tells a judge where to
look first. `--skip` takes the audit's state file and leaves out each file judged before and
unchanged since.

Three lists:

- **Slices**: every file in exactly one slice of at most `--slice-lines` lines (1,500 by
  default), a directory's files together where they fit, and a longer file in a slice of its own;
  each file with its score and signals.
- **Explicit lifecycles**: files that already type a lifecycle as a union and transition it in
  one place, the calibration candidates.
- **Lifecycle writes**: each `table.column` lifecycle write (`.update(table).set({...})`, the
  query-builder shape), with the files that write it and how many writes are blind. A column
  written from two or more files has two owners of one transition.

Lifetime signals (an async start whose premise or resource can outlive it):

  acquire     a resource acquired (`getUserMedia`, `addEventListener`, `createObjectURL`,
              `setInterval`, `subscribe(`, a socket or audio context) with fewer releases in the
              file than acquisitions, or followed by a `catch` that releases nothing
  request     a request sent (`fetcher.submit`, `fetch(`, `mutate(`) in a file that names no
              abort signal, request id or key comparison
  response    a response or callback applied to state (`fetcher.data`, `.then(`, `onSuccess`)
  timer       `setTimeout`, `AbortController`, retries
  job         work run later than its cause: queues, Durable Objects, alarms, retries, cron
  blind_write an update that sets a lifecycle column (`state`, `status`, `phase`, `stage`, a
              `*At` stamp) where its `where` does not check that column: the write trusts a
              state read earlier, which may have changed by the time it lands

Shape signals, weighted low (they also mark code that is already explicit):

  bool_state  boolean `useState`; status_cmp  `status|phase|state|step|stage|mode === "..."`;
  step_index  a wizard's step index; note  a comment narrating a lifecycle;
  fixes       fix commits on the file in the last 8 months

Another stack has no scan yet: rank its files by hand on the same signals.
"""

import collections
import json
import os
import re
import subprocess
import sys

SOURCE = re.compile(r"\.(tsx?|jsx?|mjs|cjs)$")
TEST = re.compile(r"(\.(test|spec|stories)\.|[.-]test-support\b|(^|/)(tests?|__tests__|e2e|fixtures?|"
                  r"test-support|dev-seed|seeds?)/|(^|/)seed[\w-]*\.|\.d\.ts$)")
GENERATED = re.compile(r"\.gen\.|(^|/)(generated|vendor|dist|build)/")
SCHEMA = re.compile(r"(^|/)(schema|schemas|migrations?|drizzle|prisma)(/|\.|$)", re.I)


def rx(pattern, flags=0):
    return re.compile(pattern, flags)


ACQUIRE = rx(r"\bgetUserMedia\b|\baddEventListener\(|\bcreateObjectURL\(|\bsetInterval\(|"
             r"\.subscribe\(|\bnew (?:WebSocket|EventSource|AudioContext|MediaRecorder|Worker)\b")
RELEASE = rx(r"\bremoveEventListener\(|\brevokeObjectURL\(|\bclearInterval\(|\bunsubscribe\b|"
             r"\.close\(\)|\.stop\(\)|\.disconnect\(\)|\.terminate\(\)")
REQUEST = rx(r"\bfetcher\.submit\(|\bfetch\(|\bmutate(?:Async)?\(|\.submit\(")
REQUEST_KEY = rx(r"\bAbortController\b|\bsignal\b|\brequestId\b|\brequestKey\b|\bcancelled\b|"
                 r"\bignore\b\s*=|\bisCurrent\b|\blatest\w*Ref\b")
RESPONSE = rx(r"\bfetcher\.data\b|\.then\(|\bonSuccess\b|\w+\.data\b(?=[^\n]*\bset[A-Z]\w*\()")
TIMER = rx(r"\bsetTimeout\(|\bAbortController\b|\bretry\b")
JOB = rx(r"\benqueue\w*\(|\bqueue\w*\.send|\bDurableObject\b|\balarm\b|\bscheduled\b|\bcron\b|"
         r"\bwaitUntil\(|\bjobs?\b")
UPDATE = re.compile(r"\.update\(\s*(\w+)\s*\)\s*\.set\(\s*(\{[^}]*\}|\w+)\s*\)\s*(\.where\(([^;]*?)\)\s*)?"
                    r"(?:\.(?:run|returning|execute)\(|;|$)", re.S | re.M)
LIFECYCLE_COL = re.compile(r"\b(state|status|phase|stage|[a-z][A-Za-z]*At)\b\s*:")

SHAPE = {
    "bool_state": (rx(r"useState(?:<boolean>)?\((?:true|false)\)"), 1, 5),
    "status_cmp": (rx(r"\b(?:status|phase|state|step|stage|mode)\s*[!=]==\s*[\"']"), 0.5, 8),
    "step_index": (rx(r"\b(?:currentStep|setStep|stepIndex|activeStep)\b"), 1, 4),
    "note": (rx(r"(?://|\*).*\b(?:moves? from|in flight|once it (?:stops|ends)|while (?:it|one) is|"
                r"transition)", re.I), 1, 4),
}
FIX_WEIGHT, FIX_CAP = 1, 6

UNION = rx(r"\b(?:status|phase|step|stage|state)\??\s*:\s*[\"'][\w-]+[\"']\s*\|")
TRANSITION_FN = rx(r"export function \w+\(\s*\w+\s*:\s*\w+")

ROUTINE_COLUMNS = {"createdAt", "updatedAt", "created_at", "updated_at", "deletedAt", "deleted_at",
                   "startsAt", "endsAt", "starts_at", "ends_at", "expiresAt", "expires_at"}


def git(repo, *args):
    # Unquoted paths: by default git escapes non-ASCII names in quotes, which no pattern here matches.
    return subprocess.run(["git", "-C", repo, "-c", "core.quotePath=false", *args],
                          capture_output=True, text=True, encoding="utf-8", check=True).stdout


def read(repo, path):
    try:
        with open(os.path.join(repo, path), encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return ""


def fix_counts(repo):
    log = git(repo, "log", "--since=8 months ago", "--format=@@%s", "--name-only")
    counts, in_fix = collections.Counter(), False
    for line in log.splitlines():
        if line.startswith("@@"):
            in_fix = re.match(r"@@fix\b", line) is not None
        elif line and in_fix:
            counts[line] += 1
    return counts


def unreleased_catches(text):
    """Acquisitions followed, within 20 lines, by a `catch` whose next 8 lines release nothing."""
    lines, count = text.splitlines(), 0
    for i, line in enumerate(lines):
        if not ACQUIRE.search(line):
            continue
        for j in range(i + 1, min(i + 20, len(lines))):
            if re.search(r"\bcatch\b", lines[j]):
                if not RELEASE.search("\n".join(lines[j:j + 8])):
                    count += 1
                break
    return count


def lifetime(text):
    acquired, released = len(ACQUIRE.findall(text)), len(RELEASE.findall(text))
    requests = len(REQUEST.findall(text))
    hits = {
        "acquire": (acquired - released if acquired > released else 0) + unreleased_catches(text),
        "request": requests if requests and not REQUEST_KEY.search(text) else 0,
        "response": len(RESPONSE.findall(text)),
        "timer": len(TIMER.findall(text)),
        "job": len(JOB.findall(text)),
        "blind_write": sum(blind for _, _, blind in lifecycle_writes(text)),
    }
    score = min(hits["acquire"], 3) * 4 + min(hits["request"], 3) * 3 + \
        min(hits["response"], 4) * 2 + min(hits["timer"], 4) + min(hits["job"], 4) + \
        min(hits["blind_write"], 4) * 3
    return hits, score


def judged(skip_file):
    if not skip_file or not os.path.exists(skip_file):
        return {}
    with open(skip_file, encoding="utf-8") as f:
        return {path: area["blob"] for area in json.load(f).get("judged", [])
                for path in [area["file"]]}


def blob(repo, path):
    return git(repo, "rev-parse", f"HEAD:{path}").strip()


def score_files(repo, sources):
    """{path: (score, lines, signals)} for every source file."""
    fixes = fix_counts(repo)
    scored = {}
    for path in sources:
        text = read(repo, path)
        life, score = lifetime(text)
        shape = {n: len(r.findall(text)) for n, (r, _, _) in SHAPE.items()}
        score += sum(min(shape[n], cap) * w for n, (_, w, cap) in SHAPE.items())
        score += min(fixes[path], FIX_CAP) * FIX_WEIGHT
        signals = {**{n: v for n, v in life.items() if v}, **{n: v for n, v in shape.items() if v}}
        if fixes[path]:
            signals["fixes"] = fixes[path]
        scored[path] = (score, text.count("\n") + 1, signals)
    return scored


def slices(scored, size):
    """Every file in exactly one slice of at most `size` lines, a directory's files together where
    they fit; a longer file is a slice of its own. Slices come highest score first."""
    by_dir = collections.defaultdict(list)
    for path in scored:
        by_dir[os.path.dirname(path)].append(path)
    cut = []
    for files in by_dir.values():
        files.sort(key=lambda p: -scored[p][0])
        current, lines = [], 0
        for path in files:
            n = scored[path][1]
            if current and lines + n > size:
                cut.append(current)
                current, lines = [], 0
            current.append(path)
            lines += n
        if current:
            cut.append(current)
    small = [c for c in cut if sum(scored[p][1] for p in c) < size // 3]
    merged, current, lines = [c for c in cut if c not in small], [], 0
    for c in sorted(small, key=lambda c: c[0]):
        n = sum(scored[p][1] for p in c)
        if current and lines + n > size:
            merged.append(current)
            current, lines = [], 0
        current += c
        lines += n
    if current:
        merged.append(current)
    return sorted(merged, key=lambda c: -max(scored[p][0] for p in c))


def report_slices(scored, size, skipped):
    cut = slices(scored, size)
    lines = sum(v[1] for v in scored.values())
    print(f"## Slices\n\n{len(scored)} files, {lines} lines, {len(cut)} slices of at most {size} "
          f"lines (a longer file is a slice of its own); {skipped} files judged before and "
          f"unchanged, left out.\n")
    for n, files in enumerate(cut, 1):
        top = max(scored[p][0] for p in files)
        print(f"Slice {n}: {sum(scored[p][1] for p in files)} lines, top score {top:.1f}")
        for path in files:
            score, count, signals = scored[path]
            sig = " ".join(f"{k}={v}" for k, v in signals.items())
            print(f"    {path}  {count} lines  {score:.1f}  {sig}")


def explicit(repo, sources):
    print("\n## Explicit lifecycles (calibration candidates)\n")
    found = [p for p in sources
             if UNION.search(read(repo, p)) and len(TRANSITION_FN.findall(read(repo, p))) >= 3]
    print("\n".join(found) if found else "(none found)")


def lifecycle_writes(text):
    """(table, column, blind) for each `.update(table).set({column: ...})` lifecycle write."""
    writes = []
    for table, values, _, where in UPDATE.findall(text):
        for col in LIFECYCLE_COL.findall(values):
            if col in ROUTINE_COLUMNS:
                continue
            blind = not re.search(rf"\b{table}\.{col}\b", where or "")
            writes.append((table, col, blind))
    return writes


def lifecycle_report(repo, sources):
    writers, blind = collections.defaultdict(set), collections.Counter()
    for path in sources:
        for table, col, is_blind in lifecycle_writes(read(repo, path)):
            writers[f"{table}.{col}"].add(path)
            blind[f"{table}.{col}"] += is_blind
    print("\n## Lifecycle writes (table.column: files, blind writes)\n")
    if not writers:
        print("(no `.update(table).set({...})` lifecycle writes found)")
        return
    for key in sorted(writers, key=lambda k: (-len(writers[k]), -blind[k], k)):
        files = sorted(writers[key])
        flag = "  <- several writers" if len(files) > 1 else ""
        print(f"{key}: {len(files)} files, {blind[key]} blind{flag}")
        for f in files:
            print(f"    {f}")


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        sys.exit("usage: scan.py <checkout> [--under <dir>] [--slice-lines N] [--skip <state file>]")
    repo = args[0]
    opt = lambda name, default: args[args.index(name) + 1] if name in args else default
    under, size = opt("--under", ""), int(opt("--slice-lines", 1500))
    skip = judged(opt("--skip", None))
    tracked = [p for p in git(repo, "ls-files", "-z").split("\0") if p]
    sources = [p for p in tracked if SOURCE.search(p) and not TEST.search(p)
               and not GENERATED.search(p) and p.startswith(under)]
    if not sources:
        sys.exit("no TypeScript or JavaScript sources: slice the files by hand, and rank them on "
                 "the signals in this script's docstring")
    fresh = [p for p in sources if skip.get(p) != blob(repo, p)]
    report_slices(score_files(repo, fresh), size, len(sources) - len(fresh))
    explicit(repo, sources)
    lifecycle_report(repo, sources)


if __name__ == "__main__":
    main()
