#!/usr/bin/env python3
"""Compare this run's evidence files with the last run's.

  source_watch.py <evidence dir> <copy of it from before the adapters ran> <report file> <held dir> [failed adapter ...]

A source file that lost more than half its rows is replaced by the earlier
copy: a register does not halve in a month, a broken download does. Files
the adapters did not rewrite (the adapter failed) are still last month's
and are reported as such. The report has one line per source and the word
CHECK on every line that needs a look.

It also keeps a list of the records that were in a register last run and
are gone from it this run, in <held dir>/vanished.csv, dated today. A
license that drops off an active list is the register itself saying
something ended, and unlike an "ended" list it is seen at the moment it
happens. The list is held, not used: it has to be tested first, and that
needs a few months of it. Nothing is recorded for a source that failed,
shrank by more than a fifth, or changed the way it numbers its records.
"""
import csv
import datetime
import os
import shutil
import sys

SHRANK, MOVED = 0.5, 0.2
COLUMNS = ["source", "source_id", "name", "address", "lat", "lng", "state", "date"]
csv.field_size_limit(1 << 30)


def records(path):
    """{(source, id): row} for the open records of an evidence file."""
    with open(path, newline="") as f:
        return {(r["source"], r["source_id"]): r for r in csv.DictReader(f) if r.get("state") == "open"}


def vanished(old_path, new_path):
    """Open records of the old file that the new file no longer has, or [] when the two cannot be compared."""
    old, new = records(old_path), records(new_path)
    gone = [old[k] for k in old.keys() - new.keys()]
    # a register does not lose a fifth of its entries in a month; a renumbering does
    if not old or len(gone) > len(old) * MOVED:
        return []
    return gone


def hold(rows, held_dir):
    """Add newly vanished records to the held list, keeping the day each was first missed."""
    path = os.path.join(held_dir, "vanished.csv")
    os.makedirs(held_dir, exist_ok=True)
    have = {}
    if os.path.exists(path):
        with open(path, newline="") as f:
            have = {(r["source"], r["source_id"]): r for r in csv.DictReader(f)}
    today = datetime.date.today().isoformat()
    before = len(have)
    for r in rows:
        have.setdefault((r["source"], r["source_id"]), dict(r, state="closed", date=today))
    with open(path + ".part", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(have[k] for k in sorted(have))
    os.replace(path + ".part", path)
    return len(have) - before, len(have)


def count(path):
    with open(path, "rb") as f:
        return max(sum(1 for _ in f) - 1, 0)


def main():
    cur, prev, report, held_dir = sys.argv[1:5]
    failed = set(sys.argv[5:])
    lines, gone = [], []
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
        if old is not None and "CHECK" not in note:
            missed = vanished(old_path, os.path.join(cur, name))
            gone.extend(missed)
            if missed:
                note += ", %d gone since last run" % len(missed)
        lines.append("%-24s %9d  %s" % (source, now, note))
    for a in sorted(failed):
        if not any(l.split()[0] == a or l.split()[0].startswith(a + "_") for l in lines):
            lines.append("%-24s %9s  CHECK adapter failed, no earlier file" % (a, "-"))
    lines.append("vanished records held: %d new this run, %d in all" % hold(gone, held_dir))
    os.makedirs(os.path.dirname(os.path.abspath(report)), exist_ok=True)
    with open(report, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
