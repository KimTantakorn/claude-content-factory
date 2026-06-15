# 🎬 VibeBuild — Claude Content Factory

> **Build with vibes. Ship with proof.**
> **Watch AI build 100 projects** — and turn every build into a YouTube video, Instagram Reel, and GitHub repo, automatically.

[![License: Noncommercial](https://img.shields.io/badge/license-PolyForm%20Noncommercial-blue)](LICENSE.md)
&nbsp;© 2026 VibeBuild (K.T.)

This repo has two things:

1. **[`IDEAS.md`](IDEAS.md)** — 100 curated, buildable Claude project ideas, ranked by *wow factor* and build time. Your content backlog.
2. **`devreel.py`** — **DevReel**, a tool that turns any coding session into shareable content: a screen recording, a git-history *timelapse* video, a written *recap*, and a 9:16 *reel*.

---

## Quick start

```bash
# 1. Record yourself (or Claude) building something
python devreel.py record --out builds/session.mp4

# 2. After committing your work, make a "watch it grow" timelapse
python devreel.py timelapse --repo . --out builds/timelapse.mp4 --vertical

# 3. Auto-write a recap (numbers + captions for your post)
python devreel.py recap --repo . --out builds/RECAP.md

# 4. Turn any 16:9 clip into a vertical Reel/Short
python devreel.py reel --input builds/session.mp4 --out builds/reel.mp4
```

### Requirements
- **Python 3.10+** with `Pillow` (`pip install Pillow`)
- **ffmpeg** on PATH — or set `DEVREEL_FFMPEG=C:\path\to\ffmpeg.exe`
- **git** (for timelapse + recap)

> On Windows, after `winget install Gyan.FFmpeg`, open a **new terminal** so ffmpeg is on PATH.
> DevReel also auto-detects the winget install path if PATH isn't refreshed yet.

---

## The content workflow

```
 pick an idea (IDEAS.md)
        │
        ▼
 ┌──────────────┐   record    ┌────────────────┐
 │  Claude      │ ──────────► │ session.mp4    │ ─► edit ─► YouTube
 │  builds it   │             └────────────────┘
 └──────┬───────┘
        │ commits along the way
        ▼
 ┌──────────────┐ timelapse   ┌────────────────┐
 │ git history  │ ──────────► │ timelapse.mp4  │ ─► Reels / Shorts
 └──────┬───────┘             └────────────────┘
        │
        ▼  recap
 ┌────────────────┐
 │ RECAP.md       │ ─► caption + description for every platform
 └────────────────┘
```

## Tips for going viral
- **Lead with the wow** (see the "best openers" list at the bottom of `IDEAS.md`).
- Keep Reels **under 30s**: title card → fast timelapse → the finished thing working.
- Post the repo link in the bio; the `RECAP.md` numbers ("89 commits, 4,000 lines") make great captions.
- Batch-film: build 3–4 easy ideas (#9, #13, #20, #40, #72) in one session.

---

## Roadmap
- [ ] Auto-narration via Claude API (turn `RECAP.md` into a voiceover script)
- [ ] Auto-captions burned into the reel
- [ ] One-command "build → record → timelapse → recap → publish"
- [ ] Thumbnail generator

## 📄 License

© 2026 **VibeBuild (K.T.)**. Released under the
[PolyForm Noncommercial License 1.0.0](LICENSE.md).

- ✅ **Free** for personal, educational, and nonprofit use.
- 💼 **Commercial use** (apps, products, business, revenue) **requires a paid license** — see [COMMERCIAL.md](COMMERCIAL.md) or email kimtantakorn@gmail.com.

All generated videos and recaps are watermarked `© VibeBuild (K.T.)`.

---

Built with [Claude Code](https://claude.com/claude-code).
