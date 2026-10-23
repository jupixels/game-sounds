#!/usr/bin/env python3
"""Bundle chosen sounds as base64 data URIs for single-file HTML games.

    python3 tools/embed.py jump=arcade/jump_02.mp3 coin=rpg/coins_01.mp3 \
        "step=footsteps/footstep_grass_01.mp3,footsteps/footstep_grass_02.mp3" > sounds-embedded.js

Writes JS that defines window.SFX_DATA = { name: dataURI | [dataURIs] }.
Pass it straight to sfx.load(window.SFX_DATA). Volumes from sounds.json are applied automatically.
Keep the total small (aim for under ~1 MB): pick 1-3 variants per sound.
"""
import base64
import json
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent
meta = {s["file"]: s for s in json.loads((LIB / "sounds.json").read_text())["sounds"]}
out, total = {}, 0
for arg in sys.argv[1:]:
    name, _, files = arg.partition("=")
    uris, vols = [], []
    for f in files.split(","):
        f = f.strip()
        b = (LIB / "sounds" / f).read_bytes()
        total += len(b)
        uris.append("data:audio/mpeg;base64," + base64.b64encode(b).decode())
        vols.append(meta.get(f, {}).get("volume", 1))
    out[name] = {"src": uris if len(uris) > 1 else uris[0], "volume": round(sum(vols) / len(vols), 2)}
print("window.SFX_DATA = " + json.dumps(out) + ";")
print(f"embedded {len(out)} sounds, {total / 1024:.0f} KB raw", file=sys.stderr)
