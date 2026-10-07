#!/usr/bin/env python3
"""Compare this run's evidence files with the last run's.

  source_watch.py <evidence dir> <copy of it from before the adapters ran> <report file> [failed adapter ...]

A source file that lost more than half its rows is replaced by the earlier
copy: a register does not halve in a month, a broken download does. Files
the adapters did not rewrite (the adapter failed) are still last month's
and are reported as such. The report has one line per source and the word
CHECK on every line that needs a look.
"""
import os
import shutil
import sys

SHRANK, MOVED = 0.5, 0.2


def count(path):
    with open(path, "rb") as f:
        return max(sum(1 for _ in f) - 1, 0)


def main():
    cur, prev, report = sys.argv[1:4]
    failed = set(sys.argv[4:])
    lines = []
    for name in sorted(f for f in os.listdir(cur) if f.endswith(".csv")):
        now = count(os.path.join(cur, name))
        old_path = os.path.join(prev, name)
        old = count(old_path) if os.path.exists(old_path) else None
        source = name[:-4]
        if any(source == a or source.startswith(a + "_") for a in failed):
            note = "CHECK adapter failed, last run's file kept" if old is not None else "CHECK adapter failed"
        elif old is None:
            note = "new"
        elif old and now < old * SHRANK:
            shutil.copyfile(old_path, os.path.join(cur, name))
            note = "CHECK fell from %d to %d rows, last run's file kept" % (old, now)
            now = old
        elif old and abs(now - old) > old * MOVED:
            note = "CHECK was %d rows" % old
        else:
            note = "ok"
        lines.append("%-24s %9d  %s" % (source, now, note))
    for a in sorted(failed):
        if not any(l.split()[0] == a or l.split()[0].startswith(a + "_") for l in lines):
            lines.append("%-24s %9s  CHECK adapter failed, no earlier file" % (a, "-"))
    os.makedirs(os.path.dirname(os.path.abspath(report)), exist_ok=True)
    with open(report, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
