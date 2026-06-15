#!/usr/bin/env python3
# =============================================================================
#  DevReel  —  part of VibeBuild
#  © 2026 VibeBuild (K.T.). All rights reserved.
#  Licensed under PolyForm Noncommercial 1.0.0 — see LICENSE.md.
#  Commercial use (apps, products, business) requires a paid license:
#  see COMMERCIAL.md or email complexwalk@gmail.com.
# =============================================================================
"""
DevReel - turn a coding session into shareable content.

Modes:
  record     Screen-record your work to an mp4 (Windows gdigrab / mac avfoundation / linux x11grab).
  timelapse  Build a "watch the project grow" timelapse video from git history.
  recap      Generate a written recap (Markdown) of the work from git history.
  reel       Convert any 16:9 video into a 9:16 Instagram/TikTok reel with a title card.

Designed for the "Watch Claude Build 100 Projects" content series.
Requires: ffmpeg on PATH (or set DEVREEL_FFMPEG), Pillow (pip install Pillow), git.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Windows consoles default to cp1252 and choke on emoji; force UTF-8 output.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

# ----------------------------------------------------------------------------- helpers

# Common winget install location is not on PATH until shell restart, so probe it.
_FFMPEG_FALLBACKS = [
    os.environ.get("DEVREEL_FFMPEG", ""),
    r"C:\Users\%USERNAME%\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe",
]


def find_ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    for cand in _FFMPEG_FALLBACKS:
        cand = os.path.expandvars(cand)
        if cand and Path(cand).exists():
            return cand
    # Last resort: glob the winget packages dir.
    base = Path(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages"))
    if base.exists():
        hits = list(base.glob("**/ffmpeg.exe"))
        if hits:
            return str(hits[0])
    die("ffmpeg not found. Install it (winget install Gyan.FFmpeg) or set DEVREEL_FFMPEG=path\\to\\ffmpeg.exe")


WATERMARK = "© VibeBuild (K.T.)"
BANNER = "DevReel · VibeBuild · © 2026 VibeBuild (K.T.) · Noncommercial license (see LICENSE.md)"


def die(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    print(f"[devreel] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def info(msg: str) -> None:
    print(f"[devreel] {msg}")


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    info("$ " + " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, **kw)


def git(args: list[str], repo: str) -> str:
    out = subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if out.returncode != 0:
        die(f"git {' '.join(args)} failed: {out.stderr.strip()}")
    return out.stdout


# ----------------------------------------------------------------------------- record

def cmd_record(a: argparse.Namespace) -> None:
    ff = find_ffmpeg()
    out = Path(a.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    if sys.platform.startswith("win"):
        grab = ["-f", "gdigrab", "-framerate", str(a.fps), "-i", "desktop"]
    elif sys.platform == "darwin":
        grab = ["-f", "avfoundation", "-framerate", str(a.fps), "-i", "1:none"]
    else:
        disp = os.environ.get("DISPLAY", ":0.0")
        grab = ["-f", "x11grab", "-framerate", str(a.fps), "-i", disp]

    dur = ["-t", str(a.duration)] if a.duration else []
    cmd = [ff, "-y", *grab, *dur,
           "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
           str(out)]
    info("Recording... press 'q' in this window (or Ctrl+C) to stop.")
    run(cmd)
    info(f"Saved recording -> {out}")


# ----------------------------------------------------------------------------- timelapse

def _load_font(size: int):
    from PIL import ImageFont
    candidates = [
        r"C:\Windows\Fonts\consola.ttf",      # Consolas (mono)
        r"C:\Windows\Fonts\cour.ttf",          # Courier New
        "/System/Library/Fonts/Menlo.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _render_code_frame(text: str, caption: str, w: int, h: int, out_path: Path) -> None:
    from PIL import Image, ImageDraw
    bg = (13, 17, 23)        # github dark
    fg = (201, 209, 217)
    accent = (88, 166, 255)
    img = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img)
    font = _load_font(20)
    cap_font = _load_font(26)

    # caption bar
    d.rectangle([0, 0, w, 52], fill=(22, 27, 34))
    d.text((24, 12), caption[:80], font=cap_font, fill=accent)

    # code body (truncate to what fits)
    y = 70
    line_h = 26
    max_lines = (h - y - 20) // line_h
    for ln in text.splitlines()[:max_lines]:
        d.text((24, y), ln[:110], font=font, fill=fg)
        y += line_h

    # watermark (bottom-right) — VibeBuild / author copyright
    wm_font = _load_font(18)
    wm = WATERMARK
    try:
        tw = d.textlength(wm, font=wm_font)
    except Exception:
        tw = len(wm) * 9
    d.text((w - tw - 24, h - 34), wm, font=wm_font, fill=(110, 118, 129))
    img.save(out_path)


def cmd_timelapse(a: argparse.Namespace) -> None:
    ff = find_ffmpeg()
    repo = str(Path(a.repo).resolve())
    git(["rev-parse", "--git-dir"], repo)  # ensure it's a repo

    log = git(["log", "--reverse", "--pretty=format:%H%x09%s", "--no-merges"], repo)
    commits = [ln.split("\t", 1) for ln in log.splitlines() if "\t" in ln]
    if not commits:
        die("No commits yet. Make at least one commit, then run timelapse.")
    info(f"Found {len(commits)} commits.")

    w, h = (1080, 1920) if a.vertical else (1920, 1080)
    frames_dir = Path(tempfile.mkdtemp(prefix="devreel_"))
    for i, (sha, subject) in enumerate(commits):
        # pick the largest changed text-ish file in this commit
        files = git(["show", "--name-only", "--pretty=format:", sha], repo).split()
        text = ""
        for f in files:
            if Path(f).suffix.lower() in {".py", ".js", ".ts", ".tsx", ".jsx", ".md",
                                          ".go", ".rs", ".java", ".html", ".css", ".json"}:
                try:
                    text = git(["show", f"{sha}:{f}"], repo)
                    break
                except SystemExit:
                    continue
        caption = f"#{i+1}  {subject}"
        _render_code_frame(text or subject, caption, w, h, frames_dir / f"f{i:04d}.png")

    out = Path(a.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [ff, "-y", "-framerate", str(a.fps), "-i", str(frames_dir / "f%04d.png"),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", str(out)]
    run(cmd)
    shutil.rmtree(frames_dir, ignore_errors=True)
    info(f"Saved timelapse ({len(commits)} commits) -> {out}")


# ----------------------------------------------------------------------------- recap

def cmd_recap(a: argparse.Namespace) -> None:
    repo = str(Path(a.repo).resolve())
    git(["rev-parse", "--git-dir"], repo)
    since = ["--since", a.since] if a.since else []
    log = git(["log", *since, "--pretty=format:%h%x09%ad%x09%s", "--date=short", "--no-merges"], repo)
    stat = git(["log", *since, "--shortstat", "--pretty=format:", "--no-merges"], repo)

    files_changed = sum(int(s.split()[0]) for s in stat.split("\n") if "file" in s)
    inserts = sum(int(p.split()[0]) for line in stat.split("\n") for p in line.split(",") if "insertion" in p)
    deletes = sum(int(p.split()[0]) for line in stat.split("\n") for p in line.split(",") if "deletion" in p)
    commits = [ln.split("\t") for ln in log.splitlines() if "\t" in ln]

    project = Path(repo).name
    today = dt.date.today().isoformat()
    lines = [
        f"# 🎬 Recap — {project}",
        f"_Generated {today} by DevReel_\n",
        "## By the numbers",
        f"- **{len(commits)}** commits",
        f"- **{files_changed}** file-changes  |  **+{inserts}** / **-{deletes}** lines\n",
        "## What happened",
    ]
    for sha, date, subject in commits:
        lines.append(f"- `{sha}` ({date}) — {subject}")
    lines.append("\n## Suggested captions (for Reels/Shorts)")
    lines += [
        f"- \"I let Claude build {project} from scratch 👀\"",
        f"- \"{len(commits)} commits, {inserts}+ lines, 1 AI. Watch it cook.\"",
        "- \"This took minutes, not days. #buildinpublic #ai\"",
        f"\n---\n_© {dt.date.today().year} VibeBuild (K.T.). "
        "Noncommercial use only; commercial use requires a license (COMMERCIAL.md)._",
    ]

    text = "\n".join(lines)
    out = Path(a.out).resolve()
    out.write_text(text, encoding="utf-8")
    info(f"Saved recap -> {out}")
    print("\n" + text)


# ----------------------------------------------------------------------------- reel

def cmd_reel(a: argparse.Namespace) -> None:
    ff = find_ffmpeg()
    src = Path(a.input).resolve()
    if not src.exists():
        die(f"input not found: {src}")
    out = Path(a.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    # scale to fit 1080 wide, pad to 1080x1920, center.
    vf = ("scale=1080:-2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x0d1117")
    cmd = [ff, "-y", "-i", str(src), "-vf", vf,
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(out)]
    run(cmd)
    info(f"Saved 9:16 reel -> {out}")


# ----------------------------------------------------------------------------- cli

def main() -> None:
    p = argparse.ArgumentParser(prog="devreel", description="Turn coding work into content.")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("record", help="screen record to mp4")
    r.add_argument("--out", default="session.mp4")
    r.add_argument("--fps", type=int, default=15)
    r.add_argument("--duration", type=int, default=0, help="seconds (0 = until you press q)")
    r.set_defaults(func=cmd_record)

    t = sub.add_parser("timelapse", help="git history -> growth timelapse video")
    t.add_argument("--repo", default=".")
    t.add_argument("--out", default="timelapse.mp4")
    t.add_argument("--fps", type=float, default=0.7, help="frames(commits) per second")
    t.add_argument("--vertical", action="store_true", help="9:16 instead of 16:9")
    t.set_defaults(func=cmd_timelapse)

    c = sub.add_parser("recap", help="git history -> markdown recap")
    c.add_argument("--repo", default=".")
    c.add_argument("--out", default="RECAP.md")
    c.add_argument("--since", default="", help="e.g. '1 day ago'")
    c.set_defaults(func=cmd_recap)

    e = sub.add_parser("reel", help="convert 16:9 video to 9:16 reel")
    e.add_argument("--input", required=True)
    e.add_argument("--out", default="reel.mp4")
    e.set_defaults(func=cmd_reel)

    a = p.parse_args()
    info(BANNER)
    a.func(a)


if __name__ == "__main__":
    main()
