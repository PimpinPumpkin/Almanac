"""Rows of an .xlsx sheet, with nothing but the standard library.

  rows(data, sheet=1) -> lists of cell text, one per row, gaps filled with ""

Enough for the flat tables that agencies publish: shared and inline
strings and plain numbers. Dates come back as Excel serial numbers; use
day() to turn one into an ISO date.
"""
import datetime
import io
import re
import zipfile
import xml.etree.ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _column(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


def rows(data, sheet=1):
    z = zipfile.ZipFile(io.BytesIO(data))
    strings = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.parse(z.open("xl/sharedStrings.xml")).getroot().iter(NS + "si"):
            strings.append("".join(t.text or "" for t in si.iter(NS + "t")))
    for _, row in ET.iterparse(z.open("xl/worksheets/sheet%d.xml" % sheet)):
        if row.tag != NS + "row":
            continue
        out = []
        for c in row.iter(NS + "c"):
            i = _column(c.get("r")) if c.get("r") else len(out)
            out.extend([""] * (i - len(out)))
            v = c.find(NS + "v")
            if c.get("t") == "s" and v is not None:
                text = strings[int(v.text)]
            elif c.get("t") == "inlineStr":
                text = "".join(t.text or "" for t in c.iter(NS + "t"))
            else:
                text = v.text if v is not None and v.text else ""
            out.append(text.strip())
        row.clear()
        yield out


def day(serial):
    """Excel serial date -> ISO date, or None."""
    try:
        return (datetime.date(1899, 12, 30) + datetime.timedelta(days=int(float(serial)))).isoformat()
    except (TypeError, ValueError, OverflowError):
        return None
