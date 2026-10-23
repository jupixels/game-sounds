"""Build the game sound library: rename, convert to MP3, measure, and index.

Usage: python3 -I build.py <extracted_packs_dir> <output_library_dir>
"""
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from families import RULES  # noqa: E402

SR = 44100
TARGET_RMS_DB = -20.0


def decode(path):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        check=True, capture_output=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.float32)


def channels(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels",
         "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip()
    return int(out or 1)


def db(x):
    return float(20 * np.log10(max(x, 1e-9)))


def analyze(x):
    dur = len(x) / SR
    peak = float(np.max(np.abs(x))) if len(x) else 0.0
    # trim leading/trailing silence for the "active" part
    env_thresh = peak * 10 ** (-40 / 20)
    active = np.where(np.abs(x) > env_thresh)[0]
    a = x[active[0]:active[-1] + 1] if len(active) else x
    rms = float(np.sqrt(np.mean(a ** 2))) if len(a) else 0.0

    # envelope (5 ms windows)
    w = int(SR * 0.005)
    n = max(1, len(a) // w)
    env = np.sqrt(np.mean(a[: n * w].reshape(n, w) ** 2, axis=1)) if len(a) >= w else np.array([rms])
    attack_ms = float(np.argmax(env >= 0.9 * env.max()) * 5) if env.max() > 0 else 0.0

    # spectral centroid per frame
    fsz, hop = 2048, 512
    cents, weights = [], []
    if len(a) >= fsz:
        win = np.hanning(fsz)
        freqs = np.fft.rfftfreq(fsz, 1 / SR)
        for i in range(0, len(a) - fsz, hop):
            mag = np.abs(np.fft.rfft(a[i:i + fsz] * win))
            e = mag.sum()
            if e > 0:
                cents.append(float((freqs * mag).sum() / e))
                weights.append(float(np.sqrt(np.mean(a[i:i + fsz] ** 2))))
    else:
        mag = np.abs(np.fft.rfft(a * np.hanning(len(a)))) if len(a) > 8 else np.array([1.0])
        freqs = np.fft.rfftfreq(max(len(a), 2), 1 / SR)[: len(mag)]
        cents = [float((freqs * mag).sum() / max(mag.sum(), 1e-9))]
        weights = [1.0]
    cents, weights = np.array(cents), np.array(weights)
    centroid = float(np.average(cents, weights=weights)) if weights.sum() > 0 else float(cents.mean())

    # pitch movement: tonal sounds use the dominant frequency, noisy ones the centroid
    trend = "steady"
    if len(a) >= fsz * 2:
        win = np.hanning(fsz)
        fr = np.fft.rfftfreq(fsz, 1 / SR)
        band = (fr > 80) & (fr < 5000)
        dom, flat, wts, cen = [], [], [], []
        for i in range(0, len(a) - fsz, hop):
            seg = a[i:i + fsz]
            mag = np.abs(np.fft.rfft(seg * win))
            mb = mag[band] + 1e-12
            dom.append(fr[band][np.argmax(mb)])
            flat.append(np.exp(np.mean(np.log(mb))) / np.mean(mb))
            wts.append(np.sqrt(np.mean(seg ** 2)))
            cen.append((fr * mag).sum() / max(mag.sum(), 1e-12))
        dom, flat, wts, cen = map(np.array, (dom, flat, wts, cen))
        keep = wts > wts.max() * 0.1
        tonal = np.median(flat[keep]) < 0.15 if keep.any() else False
        seq = (dom if tonal else cen)[keep]
        if len(seq) >= 4:
            start = np.median(seq[:3]) if tonal else np.median(seq[: max(1, len(seq) // 3)])
            end = np.median(seq[len(seq) // 2:]) if tonal else np.median(seq[-max(1, len(seq) // 3):])
            semis = 12 * np.log2(max(end, 1) / max(start, 1))
            if semis > 3:
                trend = "rising"
            elif semis < -3:
                trend = "falling"
    return {
        "duration": round(dur, 3),
        "peak_db": round(db(peak), 1),
        "rms_db": round(db(rms), 1),
        "attack_ms": round(attack_ms),
        "centroid_hz": round(centroid),
        "trend": trend,
    }


def describe(m):
    d = m["duration"]
    length = "very short" if d < 0.15 else "short" if d < 0.5 else "medium" if d < 1.5 else "long" if d < 4 else "very long"
    c = m["centroid_hz"]
    tone = "deep/bassy" if c < 700 else "warm" if c < 1800 else "bright" if c < 4500 else "very bright/airy"
    atk = "sharp attack" if m["attack_ms"] <= 10 else "quick attack" if m["attack_ms"] <= 60 else "slow swell"
    parts = [length, tone, atk]
    if m["trend"] != "steady":
        parts.append(f"{m['trend']} pitch")
    loud = "loud" if m["rms_db"] > -14 else "quiet" if m["rms_db"] < -28 else None
    if loud:
        parts.append(loud)
    return ", ".join(parts)


def suggested_volume(rms_db):
    v = 10 ** ((TARGET_RMS_DB - rms_db) / 20)
    return round(float(min(1.0, max(0.15, v))), 2)


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    files = sorted(p for p in src.glob("x_*/**/*.ogg") if p.name != "Preview.ogg")
    compiled = [(pk, re.compile(rx), cat, fam, desc, use) for pk, rx, cat, fam, desc, use in RULES]

    grouped = defaultdict(list)
    unmatched = []
    for f in files:
        pack = f.relative_to(src).parts[0][2:]
        for pk, rx, cat, fam, desc, use in compiled:
            if pk != pack:
                continue
            mt = rx.search(f.name)
            if mt:
                g = mt.group(1).lower() if mt.groups() else ""
                fam_n, desc_n = fam.replace("{1}", g), desc.replace("{1}", g)
                grouped[(cat, fam_n)].append((f, pack, desc_n, use))
                break
        else:
            unmatched.append(f)

    index = {"license": "CC0 1.0 (public domain). Source: Kenney.nl. Credit appreciated, not required.",
             "format": "mp3", "base_path": "sounds/", "categories": {}, "sounds": []}
    for (cat, fam), items in sorted(grouped.items()):
        items.sort(key=lambda t: t[0].name)
        catdir = out / "sounds" / cat
        catdir.mkdir(parents=True, exist_ok=True)
        for i, (f, pack, desc, use) in enumerate(items, 1):
            name = f"{fam}_{i:02d}"
            dest = catdir / f"{name}.mp3"
            stereo = channels(f) > 1 and cat == "jingles"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(f), "-ac", "2" if stereo else "1",
                            "-b:a", "128k" if stereo else "96k", str(dest)], check=True)
            m = analyze(decode(f))
            entry = {
                "id": name,
                "file": f"{cat}/{name}.mp3",
                "category": cat,
                "family": fam,
                "what_it_is": desc,
                "sounds_like": describe(m),
                "use_for": use,
                "volume": suggested_volume(m["rms_db"]),
                **m,
                "source": f"Kenney {pack} / {f.name}",
            }
            index["sounds"].append(entry)
            index["categories"].setdefault(cat, 0)
            index["categories"][cat] += 1

    (out / "sounds.json").write_text(json.dumps(index, indent=1))
    print(f"{len(index['sounds'])} sounds, categories: {index['categories']}")
    if unmatched:
        print("UNMATCHED:", [u.name for u in unmatched])


if __name__ == "__main__":
    main()
