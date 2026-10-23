"""Cut real field recordings into game clips and add them to the library (ww2/ and music/ categories).

Usage: python3 -I add_recorded.py <sources_dir> <library_dir>

<sources_dir> holds the original downloads, named as below (they are not kept in the repo; links are in CLIPS).
Each clip is cut from a source at the given times, snapped to the first transient when `snap` is set, faded,
peak-normalized to -1.5 dBFS (headroom for MP3 overshoot), encoded to MP3, measured, and written into sounds.json with its license and author.
Re-running replaces earlier ww2/music entries, so tweak a cut here and run again.

Cut points were chosen from measured loudness envelopes (tools/build/envelope.py), not by ear.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from build import SR, analyze, describe, suggested_volume  # noqa: E402

FS = "https://freesound.org/people/"
OGA = "https://opengameart.org/content/"
SOURCES = {
    "mosin": ("sounds/mosin.wav", "Tabasco", "CC0", OGA + "gunshot-sounds", "Mosin-Nagant rifle, target shooting"),
    "mg": ("110622__soundscalpelcom__warfare_gunshots_machine_gun_burst_001.wav", "soundscalpel.com", "CC-BY 3.0",
           FS + "soundscalpel.com/sounds/110622/", "machine gun burst"),
    "kent": ("170478__cheeseheadburger__distant-ww2-gunfire-kent.wav", "Cheeseheadburger", "CC-BY 4.0",
             FS + "Cheeseheadburger/sounds/170478/", "WW2 re-enactment battle heard from a wood in Kent"),
    "how1": ("161343__qubodup__howitzer-artillery-gun-shot-sound-effect-01.flac", "qubodup", "CC0",
             FS + "qubodup/sounds/161343/", "howitzer shot, from US Army footage (public domain)"),
    "how3": ("161341__qubodup__howitzer-artillery-gun-shot-sound-effect-03.flac", "qubodup", "CC0",
             FS + "qubodup/sounds/161341/", "howitzer shot, from US Army footage (public domain)"),
    "arty": ("182822__qubodup__artillery-shots.flac", "qubodup", "CC0",
             FS + "qubodup/sounds/182822/", "artillery shots, from US government footage (public domain)"),
    "siren": ("382611__nooly__air-raid-siren-prague.wav", "nooly", "CC0",
              FS + "nooly/sounds/382611/", "air-raid siren test in Prague"),
    "p47": ("143560__fight2flyphoto__p-47-flyby.wav", "Fight2FlyPhoto", "CC-BY 3.0",
            FS + "Fight2FlyPhoto/sounds/143560/", "P-47D Thunderbolt low flyby"),
    "sherman": ("368671__nicstage__sherman-e8-easy-8-tank-driving.wav", "nicStage", "CC-BY 4.0",
                FS + "nicStage/sounds/368671/", "Sherman E8 tank driving past"),
    "horn": ("181949__qubodup__fog-horn.flac", "qubodup", "CC0", FS + "qubodup/sounds/181949/", "fog horn"),
    "morse": ("34418__erh__morse-static.wav", "ERH", "CC-BY 4.0", FS + "ERH/sounds/34418/", "morse code over radio static"),
    "lament": ("Lament_of_the_War_-_Lossless_FLAC.flac", "Cethiel", "CC0", OGA + "laments-of-the-war", "Lament of the War"),
    "calltowar": ("call_to_war.wav", "Umplix", "CC0", OGA + "call-to-war", "Call to War"),
}

# (category, family, source, start, end, fade_in, fade_out, snap, stereo, description, use_for)
W = "ww2"
CLIPS = [
    (W, "rifle_shot", "mosin", 0.30, 1.35, 0, 0.35, True, False,
     "Real bolt-action rifle shot (Mosin-Nagant), crack with outdoor tail.", ["rifle fire", "infantry combat", "sniper"]),
    (W, "rifle_shot", "mosin", 3.38, 4.40, 0, 0.35, True, False, None, None),
    (W, "rifle_shot", "mosin", 5.85, 6.90, 0, 0.35, True, False, None, None),
    (W, "rifle_shot", "mosin", 8.62, 9.65, 0, 0.35, True, False, None, None),
    (W, "mg_burst", "mg", 0.00, 2.45, 0, 0.45, True, True,
     "Machine-gun burst (about 0.7 s of fire) with echo tail.", ["machine gun", "infantry combat", "strafing"]),
    (W, "mg_burst", "mg", 0.33, 2.45, 0.005, 0.45, True, True, None, None),
    (W, "battle_distant", "kent", 0.00, 4.50, 0.15, 0.9, False, False,
     "Distant WW2 battle: rifles and machine guns crackling through trees.", ["battle ambience", "land battle", "front line"]),
    (W, "battle_distant", "kent", 7.30, 11.00, 0.15, 0.9, False, False, None, None),
    (W, "battle_distant", "kent", 24.40, 29.00, 0.15, 0.9, False, False, None, None),
    (W, "battle_distant", "kent", 53.40, 58.00, 0.15, 0.9, False, False, None, None),
    (W, "howitzer", "how1", 0.00, 0.80, 0, 0.12, True, False,
     "Close howitzer firing: hard boom with short decay.", ["artillery", "cannon", "tank gun"]),
    (W, "howitzer", "how3", 0.00, 1.40, 0, 0.25, True, False, None, None),
    (W, "artillery", "arty", 0.35, 2.10, 0, 0.3, True, False,
     "Field artillery shot with rolling echo.", ["artillery barrage", "bombardment", "naval guns"]),
    (W, "artillery", "arty", 2.35, 3.70, 0, 0.3, True, False, None, None),
    (W, "artillery", "arty", 3.85, 5.30, 0, 0.3, True, False, None, None),
    (W, "artillery", "arty", 5.60, 6.95, 0, 0.3, True, False, None, None),
    (W, "artillery", "arty", 7.10, 9.45, 0, 0.4, True, False, None, None),
    (W, "artillery", "arty", 9.80, 12.70, 0, 0.5, True, False, None, None),
    (W, "air_raid_siren", "siren", 40.20, 48.40, 0.6, 1.5, False, False,
     "Real air-raid siren, steady wail (about 8 s).", ["air raid", "bombing alert", "war declared"]),
    (W, "air_raid_siren", "siren", 0.60, 9.00, 0.3, 1.5, False, False, None, None),
    (W, "plane_flyby", "p47", 3.00, 11.45, 1.0, 1.0, False, True,
     "Piston warplane (P-47 Thunderbolt) approaching and roaring overhead, stereo.", ["plane flyover", "air raid", "air battle"]),
    (W, "plane_pass", "p47", 5.60, 9.60, 0.6, 1.2, False, True,
     "Short piston-plane pass (4 s), the loudest part of the flyby.", ["plane built", "air unit", "quick flyover"]),
    (W, "tank_pass", "sherman", 42.00, 55.00, 1.0, 1.5, False, False,
     "Sherman tank driving past: engine roar and track clatter (13 s).", ["tank column", "armored attack"]),
    (W, "tank_rumble", "sherman", 45.50, 49.50, 0.2, 1.0, False, False,
     "Close Sherman tank engine and tracks (4 s).", ["tank built", "armor moves"]),
    (W, "tank_rumble", "sherman", 49.50, 53.50, 0.2, 1.0, False, False, None, None),
    (W, "ship_horn", "horn", 0.00, 3.00, 0.02, 0.2, False, False,
     "Deep ship fog horn blast.", ["ship", "fleet moves", "naval landing"]),
    (W, "radio_morse", "morse", 0.05, 4.75, 0, 0.1, False, False,
     "Radio click, then morse code over static.", ["orders sent", "radio message", "intel"]),
    (W, "radio_morse", "morse", 0.90, 2.70, 0.05, 0.4, False, False, None, None),
    ("music", "war_lament", "lament", 0, None, 0, 0, False, True,
     "Orchestral war lament (3:48), somber and slow. Loops.", ["menu music", "strategy map", "sad or serious mood"]),
    ("music", "call_to_war", "calltowar", 0, None, 0, 0, False, True,
     "Orchestral battle theme with snare and horns (1:16). Loops.", ["battle music", "war time", "action"]),
]


def load(path, stereo):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "2" if stereo else "1", "-ar", str(SR),
                          "-f", "f32le", "-"], check=True, capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).copy()
    return x.reshape(-1, 2) if stereo else x.reshape(-1, 1)


def snap_start(x, i0, i1):
    """Move the start to just before the first transient (frame 12 dB over the running floor)."""
    mono = np.abs(x[i0:i1]).mean(axis=1)
    f = int(0.005 * SR)
    if len(mono) < f * 4:
        return i0
    e = np.sqrt(np.convolve(mono ** 2, np.ones(f) / f, mode="valid"))[::f] + 1e-9
    d = 20 * np.log10(e)
    top = d.max()
    for k in range(len(d)):
        if d[k] > top - 12:
            return i0 + max(0, k * f - int(0.008 * SR))
    return i0


def cut(src, c):
    cat, fam, key, s, e, fi, fo, snap, stereo = c[:9]
    x = load(src, stereo)
    i0 = int(s * SR)
    i1 = len(x) if e is None else min(len(x), int(e * SR))
    if snap:
        i0 = snap_start(x, i0, i1)
    y = x[i0:i1].copy()
    fade_in = max(int(fi * SR), int(0.003 * SR))  # always a few ms so cuts never click
    y[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
    if fo:
        n = int(fo * SR)
        y[-n:] *= (np.linspace(1, 0, n) ** 2)[:, None]
    peak = np.abs(y).max()
    if peak > 0:
        y *= 10 ** (-1.5 / 20) / peak
    return y


def main():
    srcdir, lib = Path(sys.argv[1]), Path(sys.argv[2])
    data = json.loads((lib / "sounds.json").read_text())
    data["sounds"] = [s for s in data["sounds"] if s["category"] not in ("ww2", "music")]
    count, last = {}, {}
    for c in CLIPS:
        cat, fam, key = c[0], c[1], c[2]
        desc, use = c[9] or last[fam][0], c[10] or last[fam][1]
        last[fam] = (desc, use)
        fname, author, lic, url, what = SOURCES[key]
        y = cut(srcdir / fname, c)
        count[fam] = count.get(fam, 0) + 1
        name = f"{fam}_{count[fam]:02d}"
        dest = lib / "sounds" / cat / f"{name}.mp3"
        dest.parent.mkdir(parents=True, exist_ok=True)
        stereo = y.shape[1] == 2
        rate = "112k" if cat == "music" else ("128k" if stereo else "96k")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", str(y.shape[1]),
                        "-i", "-", "-b:a", rate, str(dest)], input=y.astype(np.float32).tobytes(), check=True)
        m = analyze(y.mean(axis=1))
        data["sounds"].append({
            "id": name, "file": f"{cat}/{name}.mp3", "category": cat, "family": fam,
            "what_it_is": desc, "sounds_like": describe(m), "use_for": use,
            "volume": 0.4 if cat == "music" else suggested_volume(m["rms_db"]), **m,
            "source": f"{author}: {what}" + ("" if c[4] is None else f", {c[3]:.2f}-{c[4]:.2f}s"),
            "license": lic, "author": author, "source_url": url,
        })
        print(f"{dest.relative_to(lib)}  {m['duration']:.2f}s  rms {m['rms_db']}  {lic}")
    cats = {}
    for s in data["sounds"]:
        cats[s["category"]] = cats.get(s["category"], 0) + 1
    data["categories"] = cats
    data["license"] = ("Kenney.nl sounds are CC0. The ww2/ and music/ recordings are CC0 or CC-BY: each entry has its own "
                       "license, author and source_url, and CC-BY sounds need a credit line in your game (see LICENSE.md).")
    (lib / "sounds.json").write_text(json.dumps(data, indent=1))
    print(len(data["sounds"]), "sounds;", cats)


if __name__ == "__main__":
    main()
