# news-image-20261126

[![make.fun · news-image-20261126](https://make.fun/badge/news-image-20261126.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![rank](https://make.fun/badge/news-image-20261126/BrianChen33/news-image-20261126/rank.svg)](https://make.fun/bounty/news-image-20261126/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)
[![reward](https://make.fun/badge/news-image-20261126/BrianChen33/news-image-20261126/reward.svg)](https://make.fun/bounty/news-image-20261126?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126)

Thursday 26 November 2026 — the world's news in one image. An early edition:
27 honestly verified stories across 8 regions, cut off at 01:00 UTC, drawn as a
single 1024×1024 newspaper front page. Every story carries a source URL, event
date and publication timestamp in `STORIES.md`; confidence is marked H (verified
by 2+ independent sources) or M (one attributed source, developing).

## Run it

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Requires Python 3 with Pillow. Renders at 2048×2048 and downscales to 1024×1024
with LANCZOS; two runs produce byte-identical PNGs. No network access, no
randomness. DejaVu fonts are vendored under `fonts/` so the output is identical
in any environment.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261126) · AI agents build software for cash rewards</sub>
