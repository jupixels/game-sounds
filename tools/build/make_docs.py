"""Add quick picks to sounds.json and generate CATALOG.md + preview.html.

Usage: python3 -I make_docs.py <library_dir>
"""
import html
import json
import sys
from pathlib import Path

lib = Path(sys.argv[1])
data = json.loads((lib / "sounds.json").read_text())
by_id = {s["id"]: s for s in data["sounds"]}
by_fam = {}
for s in data["sounds"]:
    by_fam.setdefault(s["family"], []).append(s)

# Starting suggestions per game event: family names (all variants) or specific ids.
PICKS = {
    "ui_click": ["click"], "ui_hover": ["hover"], "ui_confirm": ["confirm"], "ui_error": ["error"],
    "ui_back": ["back"], "menu_open": ["open"], "menu_close": ["close"], "ui_toggle": ["toggle"],
    "notification": ["glass"], "typewriter_text": ["tick"],
    "jump": ["jump_02", "jump_03"], "land": ["soft_medium"], "bounce": ["generic_light"],
    "coin_realistic": ["coins"], "coin_arcade": ["three_tone", "two_tone"], "gem_pickup": ["glass"],
    "item_pickup": ["pep"], "power_up": ["power_up_10", "power_up_11", "power_up_12"],
    "shoot_laser": ["laser_small"], "shoot_heavy": ["laser_large"], "shoot_retro": ["laser_retro"],
    "shoot_synth": ["laser"], "explosion_small": ["explosion_crunch"], "explosion_big": ["explosion_deep"],
    "hit_enemy": ["punch_medium"], "player_hurt": ["punch_heavy"], "lose_life": ["zap_three_down_01", "phaser_down"],
    "sword_clash": ["metal_medium"], "sword_draw": ["draw_blade"], "sword_slash": ["slice"],
    "shield": ["force_field"], "dash_boost": ["thruster"], "ship_hit": ["hull_impact"],
    "engine_loop": ["engine_small"], "slime": ["slime"], "mining": ["mining"], "chop_wood": ["chop"],
    "door_open": ["door_open"], "door_close": ["door_close"], "chest_open": ["creak", "metal_latch"],
    "footsteps_grass": ["footstep_grass"], "footsteps_stone": ["footstep_concrete"], "footsteps_wood": ["footstep_wood"],
    "footsteps_dirt": ["footstep_dirt"], "footsteps_snow": ["footstep_snow"],
    "card_deal": ["card_slide"], "card_play": ["card_place"], "shuffle": ["card_shuffle"], "dice_roll": ["dice"],
    "bet_chips": ["chips"], "unlock_success": ["zap_three_up_01"],
    "jingle_win_or_lose": ["jingle_8bit", "jingle_pizzicato"], "stinger": ["jingle_hit"],
    # realistic war sounds (ww2/) and recorded music (music/); some are CC-BY, see each entry's license
    "gunfire_realistic": ["rifle_shot", "mg_burst"], "battle_ambience": ["battle_distant"],
    "artillery": ["artillery"], "cannon_or_tank_gun": ["howitzer"], "air_raid_siren": ["air_raid_siren"],
    "plane_flyover": ["plane_flyby", "plane_pass"], "tank": ["tank_rumble", "tank_pass"], "ship_horn": ["ship_horn"],
    "radio_morse": ["radio_morse"], "music_somber": ["war_lament"], "music_battle": ["call_to_war"],
}
quick = {}
for event, refs in PICKS.items():
    files = []
    for r in refs:
        if r in by_id:
            files.append(by_id[r]["file"])
        elif r in by_fam:
            files.extend(s["file"] for s in by_fam[r])
        else:
            raise SystemExit(f"unknown pick {r}")
    quick[event] = files
data["quick_picks"] = quick
data["quick_picks_note"] = "Starting suggestions chosen from names and measurements, not by ear. Jingles in particular must be auditioned (preview.html) to know which sound happy vs sad."
(lib / "sounds.json").write_text(json.dumps(data, indent=1))

# ---- CATALOG.md: compact, readable by Claude and humans ----
lines = ["# Sound catalog", "",
         f"{len(data['sounds'])} sounds. Kenney.nl sounds are CC0. The `ww2/` recordings and `music/` tracks are CC0 or CC-BY "
         "(license and author on each line; CC-BY needs a credit line in your game, see LICENSE.md). Files are `sounds/<file>`. "
         "`vol` = suggested volume (0–1) so sounds mix evenly. Descriptions after the dash are measured from the audio "
         "(length, brightness, attack, pitch direction) and are approximate.", ""]
lines += ["## Quick picks (game event → files)", ""]
for ev, files in quick.items():
    shown = ", ".join(f"`{f}`" for f in files[:4]) + (f" (+{len(files) - 4} more variants)" if len(files) > 4 else "")
    lines.append(f"- **{ev}**: {shown}")
lines.append("")
cat = None
for fam, items in sorted(by_fam.items(), key=lambda kv: (kv[1][0]["category"], kv[0])):
    if items[0]["category"] != cat:
        cat = items[0]["category"]
        lines += [f"## {cat}", ""]
    s0 = items[0]
    lines.append(f"### {fam} — {s0['what_it_is']} Use for: {', '.join(s0['use_for'])}.")
    for s in items:
        lic = f" [{s['license']}, {s['author']}]" if "license" in s else ""
        lines.append(f"- `{s['file']}` {s['duration']:.2f}s, vol {s['volume']} — {s['sounds_like']}{lic}")
    lines.append("")
(lib / "CATALOG.md").write_text("\n".join(lines))

# ---- preview.html: audition page ----
rows = []
for s in data["sounds"]:
    rows.append({"f": s["file"], "c": s["category"], "fam": s["family"], "w": s["what_it_is"],
                 "l": s["sounds_like"] + (f" · {s['license']} by {s['author']}" if "license" in s else ""), "v": s["volume"], "d": s["duration"]})
page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Game Sound Preview</title><style>
:root{--bg:#f6f5f2;--fg:#1d1d1b;--mut:#6b6a66;--card:#fff;--line:#e3e1dc;--acc:#2f6fdf;--fav:#e0a100}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ecebe7;--mut:#9d9b95;--card:#20201e;--line:#33322f;--acc:#6b9cff;--fav:#ffc533}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.4 system-ui,-apple-system,Segoe UI,sans-serif}
header{position:sticky;top:0;background:var(--bg);padding:16px;border-bottom:1px solid var(--line);z-index:2}
h1{font-size:20px;margin:0 0 4px}p{margin:0 0 10px;color:var(--mut)}
.bar{display:flex;gap:8px;flex-wrap:wrap}input,select,button{font:inherit;color:var(--fg);background:var(--card);border:1px solid var(--line);border-radius:8px;padding:7px 10px}
input{flex:1;min-width:180px}main{padding:16px;max-width:1100px;margin:0 auto}
.fam{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin-bottom:10px}
.fam h3{margin:0 0 2px;font-size:15px}.fam .w{color:var(--mut);font-size:13px;margin-bottom:8px}
.btns{display:flex;flex-wrap:wrap;gap:6px}.s{display:flex;align-items:center;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.s button{border:0;border-radius:0;padding:6px 10px;cursor:pointer;background:transparent}.s button.p:hover{background:var(--acc);color:#fff}
.s button.st{color:var(--mut);padding:6px 8px;border-left:1px solid var(--line)}.s button.st.on{color:var(--fav)}
.tag{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em}
#favs{white-space:pre-wrap;font:12px ui-monospace,monospace;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px;margin-top:8px;display:none}
</style></head><body><header><h1>Game Sound Preview</h1>
<p>Click a sound to hear it (hover over it to see what it is). Star favorites, then copy the list into a chat with Claude.</p>
<div class="bar"><input id="q" placeholder="Search: laser, coin, jump, footstep…"><select id="cat"><option value="">All categories</option></select>
<button id="copy">Copy starred list</button></div><div id="favs"></div></header><main id="list"></main>
<script>
const S=__DATA__;const favs=new Set(JSON.parse((()=>{try{return localStorage.getItem('favs')||'[]'}catch(e){return '[]'}})()));
const save=()=>{try{localStorage.setItem('favs',JSON.stringify([...favs]))}catch(e){}};
const cats=[...new Set(S.map(s=>s.c))];const sel=document.getElementById('cat');cats.forEach(c=>sel.add(new Option(c,c)));
let cur;function play(s){if(cur){cur.pause()}cur=new Audio('sounds/'+s.f);cur.volume=s.v;cur.play()}
function render(){const q=document.getElementById('q').value.toLowerCase().split(/\\s+/).filter(Boolean),c=sel.value;
const L=document.getElementById('list');L.innerHTML='';const fams={};
S.filter(s=>(!c||s.c===c)&&q.every(w=>(s.f+' '+s.w+' '+s.l).toLowerCase().includes(w))).forEach(s=>(fams[s.fam]=fams[s.fam]||[]).push(s));
for(const [f,items] of Object.entries(fams)){const d=document.createElement('div');d.className='fam';
d.innerHTML=`<div class="tag">${items[0].c}</div><h3>${f}</h3><div class="w">${items[0].w}</div><div class="btns"></div>`;
const b=d.querySelector('.btns');items.forEach(s=>{const w=document.createElement('div');w.className='s';
const p=document.createElement('button');p.className='p';p.textContent='▶ '+s.f.split('/')[1].replace('.mp3','');p.title=s.l+' · '+s.d+'s';p.onclick=()=>play(s);
const st=document.createElement('button');st.className='st'+(favs.has(s.f)?' on':'');st.textContent='★';st.title='Star';
st.onclick=()=>{favs.has(s.f)?favs.delete(s.f):favs.add(s.f);st.classList.toggle('on');save()};w.append(p,st);b.append(w)});L.append(d)}
if(!L.children.length)L.innerHTML='<p>No sounds match.</p>'}
document.getElementById('q').oninput=render;sel.onchange=render;
document.getElementById('copy').onclick=()=>{const t='My favorite sounds from game-sounds:\\n'+[...favs].map(f=>'- '+f).join('\\n');
const box=document.getElementById('favs');box.style.display='block';box.textContent=t;try{navigator.clipboard.writeText(t)}catch(e){}};
render();
</script></body></html>"""
(lib / "preview.html").write_text(page.replace("__DATA__", json.dumps(rows)))
print("docs written;", len(quick), "quick picks")
