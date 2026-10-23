#!/usr/bin/env python3
"""Search the sound library by keyword.

    python3 tools/find.py jump              # anything matching "jump"
    python3 tools/find.py coin pickup       # all words must match
    python3 tools/find.py --cat impacts metal
    python3 tools/find.py --families        # one line per family (overview)

Matches id, family, category, what_it_is, sounds_like and use_for.
"""
import json
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent
data = json.loads((LIB / "sounds.json").read_text())
args = sys.argv[1:]

if "--families" in args:
    fams = {}
    for s in data["sounds"]:
        f = fams.setdefault(s["family"], {"cat": s["category"], "n": 0, "what": s["what_it_is"], "use": s["use_for"]})
        f["n"] += 1
    for name, f in sorted(fams.items(), key=lambda kv: (kv[1]["cat"], kv[0])):
        print(f"{f['cat']:<10} {name:<22} x{f['n']:<3} {f['what']}  use: {', '.join(f['use'])}")
    sys.exit()

cat = None
if "--cat" in args:
    i = args.index("--cat")
    cat = args[i + 1]
    args = args[:i] + args[i + 2:]
words = [w.lower() for w in args]

for s in data["sounds"]:
    if cat and s["category"] != cat:
        continue
    hay = " ".join([s["id"], s["family"], s["category"], s["what_it_is"], s["sounds_like"], " ".join(s["use_for"])]).lower()
    if all(w in hay for w in words):
        print(f"{s['file']:<38} {s['duration']:>5.2f}s vol {s['volume']:<4}  {s['what_it_is']} [{s['sounds_like']}]")
