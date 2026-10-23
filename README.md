# game-sounds

A ready-to-use library of **636 real game sound effects, jingles and music tracks**, organized and described so Claude (or anyone) can pick the right sound without hearing it. 606 are **CC0 / public domain** from [Kenney.nl](https://kenney.nl), free for personal and commercial games with no credit required (credit is appreciated). The `ww2` and `music` folders hold real recordings from Freesound and OpenGameArt; some of those are CC-BY and need a credit line (see `LICENSE.md`).

## What's inside

| Folder | Count | What |
|---|---|---|
| `sounds/ui` | 151 | clicks, hovers, confirm, error, open/close, toggles, ticks |
| `sounds/impacts` | 105 | punches, thuds, wood, metal, glass, armor, bells, mining |
| `sounds/jingles` | 85 | short music stingers: 8-bit, orchestral hits, pizzicato, sax, steel drum |
| `sounds/scifi` | 73 | lasers, explosions, shields, thrusters, engines, sci-fi doors |
| `sounds/arcade` | 62 | retro synth jumps, power-ups, zaps, coins, blips |
| `sounds/tabletop` | 54 | cards, chips, dice |
| `sounds/rpg` | 41 | doors, coins, blades, books, cloth, leather |
| `sounds/footsteps` | 35 | grass, concrete, wood, snow, carpet, dirt |
| `sounds/ww2` | 28 | real recordings: rifle shots, machine guns, distant battle, artillery, howitzer, air-raid siren, warplane flyby, Sherman tank, ship horn, morse radio |
| `sounds/music` | 2 | orchestral loops: a somber war lament (3:48) and a battle theme (1:16) |

All files are MP3 (plays in every browser), mono for effects and stereo for jingles, music and the two flyby/machine-gun recordings. Most families come with several variants so repeated sounds don't feel robotic.

## Files

- **`CATALOG.md`**: the human- and Claude-readable list. It starts with quick picks (game event → sound), then every family with a description of each file.
- **`sounds.json`**: the same data in machine-readable form: what each sound is, what it sounds like (length, brightness, attack, pitch direction, all measured from the audio), what to use it for, and a suggested volume so sounds mix evenly.
- **`preview.html`**: open it in a browser to listen to everything. Star your favorites and copy the list to tell Claude which ones you like.
- **`lib/sfx.js`**: a small audio manager (no dependencies) that preloads, plays random variants, varies pitch slightly, loops engines and music, and handles the browser's "audio needs a click first" rule.
- **`tools/find.py`**: search from the command line: `python3 tools/find.py laser`.
- **`tools/embed.py`**: packs chosen sounds into a JS file of data URIs for single-file HTML games.
- **`tools/build/`**: the scripts that built this library, for adding more packs later. `add_recorded.py` cuts long field recordings into clips (the `ww2` and `music` sets), and `envelope.py` prints a loudness timeline so cut points can be chosen without listening.

## Using it in a game

```html
<script src="lib/sfx.js"></script>
<script>
  const sfx = new SFX({ base: "sounds/" });
  sfx.load({
    jump: { src: ["arcade/jump_02.mp3", "arcade/jump_03.mp3"], volume: 0.4 },
    coin: { src: "rpg/coins_01.mp3", volume: 1 },
    step: ["footsteps/footstep_grass_01.mp3", "footsteps/footstep_grass_02.mp3", "footsteps/footstep_grass_03.mp3"],
  });
  // later, in game code:
  sfx.play("jump");
  sfx.play("step", { vary: 0.08, volume: 0.6 });
</script>
```

**From GitHub without copying files:** once this repo is on GitHub, any game can load sounds through jsDelivr's free CDN:
`new SFX({ base: "https://cdn.jsdelivr.net/gh/<your-username>/game-sounds@main/sounds/" })`

**Single-file HTML game:** `python3 tools/embed.py jump=arcade/jump_02.mp3 coin=rpg/coins_01.mp3 > sounds-embedded.js`, then paste that output and `sfx.js` into the page and call `sfx.load(window.SFX_DATA)`.

## Adding more sounds

Drop new files into a category folder and add entries to `sounds.json`, or extend `tools/build/families.py` and re-run the build. Other good CC0 sources include more Kenney packs, OpenGameArt (filter by CC0), and Freesound (filter by CC0).

## License

The Kenney.nl audio is CC0 1.0. The `ww2` and `music` recordings are CC0 or CC-BY 3.0/4.0, listed per file in `LICENSE.md` and `sounds.json`. The code in `lib/` and `tools/` is released as CC0.
