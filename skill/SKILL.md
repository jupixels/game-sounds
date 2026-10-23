---
name: game-audio
description: Use whenever building or editing a game, interactive toy, or animated web page that needs sound effects or music, in a single HTML file, an artifact, or a repo. Uses the user's real sound library instead of synthesized beeps.
---

# Game audio with the game-sounds library

The user has a library of 606 real, CC0 game sounds (Kenney.nl) in the GitHub repo **jupixels/game-sounds**.
Always use it for game audio. Do not synthesize sound effects with oscillators unless the user asks for
procedural audio or no library sound fits (then say so).

You cannot hear audio. Choose sounds from the written descriptions, never from filenames alone.

## 1. Get the library

- If the project already contains a `game-sounds/` folder or the repo is already checked out, use that.
- Otherwise attach and clone it: `git clone --depth 1 https://github.com/jupixels/game-sounds.git /tmp/game-sounds`
  (in Claude.ai, attach the repo first with the add-repo tool).
- Key files: `CATALOG.md` (read the "Quick picks" section first, then the families you need),
  `sounds.json` (full data, including `quick_picks`), `lib/sfx.js` (the audio manager),
  `tools/find.py` (search: `python3 tools/find.py laser`), and `tools/embed.py` (data-URI bundler).

## 2. Choose sounds

1. Make a list of the game's sound events (shoot, hit, pickup, jump, menu click, win, lose, music...).
2. For each event, start from `quick_picks` in CATALOG.md, then check family descriptions and `sounds_like`
   (length, brightness, attack, pitch direction) to match the game's feel:
   - Retro or pixel-art games: prefer `arcade/`, `scifi/laser_retro`, and `jingles/jingle_8bit`.
   - Realistic, fantasy, or RPG games: prefer `impacts/`, `rpg/`, `footsteps/`, `jingles/jingle_hit`.
   - Cute or casual games: prefer `ui/pluck`, `ui/glass`, `arcade/pep`, `jingles/jingle_pizzicato`.
   - Card and board games: `tabletop/`.
3. Load 2 to 4 variants for anything that repeats often (footsteps, shots, hits, coins) so repeats sound natural.
4. Use each sound's suggested `volume` from sounds.json as its base volume.
5. Jingles were labeled by measurement, not by ear, so whether one sounds happy or sad is unknown. Rising
   pitch usually suits a win and falling pitch a loss. If the user has starred favorites, use those.
6. If the user names specific files (for example from `preview.html`), use exactly those.

## 3. Wire it in

Always use `lib/sfx.js`. Copy it into the project; don't rewrite it.

```js
const sfx = new SFX({ base: "sounds/" });
await sfx.load({
  shoot: { src: ["scifi/laser_small_01.mp3", "scifi/laser_small_02.mp3"], volume: 0.5 },
  coin:  { src: "rpg/coins_01.mp3", volume: 1 },
});
sfx.play("shoot", { vary: 0.06, pan: x / width * 2 - 1 });   // vary = small random pitch change
const eng = sfx.loop("engine"); eng.stop(0.3);                  // loops: engines, ambience
sfx.music("theme");                                             // looping music bus with crossfade
sfx.setVolume("master", 0);                                     // mute button
```

Choose the delivery method by where the game lives:

| Where the game lives | How to include sounds |
|---|---|
| A repo or multi-file project | Copy only the MP3s you use into `sounds/<category>/` in the project, plus `lib/sfx.js`. Add a line crediting Kenney.nl (CC0) in the README. |
| A single HTML file the user downloads | Run `python3 tools/embed.py name=path ... > sounds-embedded.js`, then inline that output and sfx.js into the page and call `sfx.load(window.SFX_DATA)`. Keep embedded audio under about 1 MB. |
| A published Claude artifact | Embed the sounds the same way as a single HTML file. Artifacts can't load audio from other sites. |
| A page hosted elsewhere (e.g. GitHub Pages) | You may load from jsDelivr instead of copying: `base: "https://cdn.jsdelivr.net/gh/jupixels/game-sounds@main/sounds/"`. |

## 4. Mixing rules

- Browsers block audio until the first click or key press. sfx.js unlocks itself, but start the game
  from a "click/press to start" screen so the first sounds aren't lost.
- Keep UI sounds quieter than gameplay sounds, and music around 0.3 to 0.5.
- Use `cooldown` (default 0.03s) or a longer value to stop rapid-fire events from stacking into noise.
- Pan positional sounds with `pan` and add `vary` to anything that repeats.
- Always add a mute/volume toggle (M key or an on-screen button).
- After building, list the sounds used (event → file) in your reply so the user can ask to swap any of them.
