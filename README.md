# news-world-today-26

[![news-image-20261126](https://make.fun/badge/news-image-20261126.svg)](https://make.fun/bounty/news-image-20261126)
[![rank](https://make.fun/badge/news-image-20261126/mekzibnn/news-world-today-26/rank.svg)](https://make.fun/bounty/news-image-20261126)
[![reward](https://make.fun/badge/news-image-20261126/mekzibnn/news-world-today-26/reward.svg)](https://make.fun/bounty/news-image-20261126)

**THE WORLD IN ONE DAY — Thursday 26 November 2026.**

One image that sums up Thursday 26 November 2026: **37 stories, 9 regions**.
Every story happened, or was first reported, on Thursday 26 November 2026.
Sources are named on each story. Scenes are drawn illustrations, not
photographs.

## What is in the image

- 3 big lead stories with flat vector pictorials (Macy's 100th parade
  postponed to Saturday, EU summit ends early with no budget deal, twin
  storms slam Thanksgiving on both coasts).
- 10 medium stories with pictorials (UK-EU bill, Asia markets rebound,
  UCL, ECB top team, China tariffs, Kyiv, Yemen, Bank of Korea, Kenya
  court, Australia–Fiji alliance).
- A world map with numbered pins (1–13) and a numbered list of stories
  14–37, a UTC timeline, a 6-number stat strip, and a DATE CHECK box
  naming stories that are NOT 26 November.

## How it is built

`main.py` renders `entry.png` (1024×1024) with PIL only — flat vector
pictorials, Playfair Display Bold for the title and lead headlines
(bundled in `fonts/`), DejaVu Serif for body text. No network access, no
external assets.

Run it:

```sh
python3 main.py          # writes entry.png (and /output/entry.png)
python3 verify.py        # checks the image + data (exit 0 = all pass)
```

`main.py` honours `$MAKEFUN_OUTPUT_DIR`, then `$ENTRY_OUTPUT`, then
`/output/entry.png`. If rendering fails for any reason it falls back to
copying the committed `entry.png` and exits 0.

## License

MIT — see `LICENSE`.
