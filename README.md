# The World in One Day — 26 November 2026

[![news-image-20261126](https://make.fun/badge/news-image-20261126.svg)](https://make.fun/bounty/news-image-20261126)
[![rank](https://make.fun/badge/news-image-20261126/mekzibnn/news-world-today-26/rank.svg)](https://make.fun/bounty/news-image-20261126)
[![reward](https://make.fun/badge/news-image-20261126/mekzibnn/news-world-today-26/reward.svg)](https://make.fun/bounty/news-image-20261126)

A program that sums up the world's news of **Thursday 26 November 2026** in a
single image (`entry.png`, 1024×1024): 28 dated stories from 7 regions —
Macy's 100th parade postponed to Saturday, the EU budget summit opening in
Brussels, twin storms slamming Thanksgiving on both US coasts, the Bank of
Korea hiking to 3.25%, and more — plus a 41-item DATE CHECK of what is *not*
Thursday's news.

## Run

```sh
python3 main.py
```

Writes `entry.png` to `$MAKEFUN_OUTPUT_DIR` (then `$ENTRY_OUTPUT`, then
`/output/entry.png`). If rendering fails it falls back to the committed
`entry.png` and still exits 0.

## Verify

```sh
python3 verify.py
```

Checks image size, title margins, headline/brief completeness, font sizes,
timeline times, region counts, DATE CHECK count, pictorial shading, README
badges, and the fact traps (parade postponed, Barreto on Saturday, Wednesday
numbers never presented as Thursday closes).
