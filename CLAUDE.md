# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Claude Context

### Personal context
For preferences and working style, always read these files from the skips-brain repo before starting work:
- `about-skip.md`
- `preferences.md`

---

## Project Overview

Two standalone Python CLI scripts for analyzing audio mixes. No framework, no package structure, no build system — just two files that run directly with `python`.

- **`mix_fingerprint.py`** — acoustic analysis → `mix_fingerprint.json`
- **`transcribe_mix.py`** — Whisper speech-to-text → `mix_transcript.txt`

## Running the Scripts

Both scripts auto-install their Python dependencies on first run. The only manual prerequisite is `ffmpeg` on the system PATH.

```bash
python mix_fingerprint.py
python transcribe_mix.py
```

**Before running**, edit the hardcoded filename near the top of each script:
- `mix_fingerprint.py` line 20: `audio_file = "your_mix.mp3"`
- `transcribe_mix.py` line 18: `audio_file = "your_file.mp3"`

Both scripts accept any audio format ffmpeg supports (MP3, WAV, FLAC, M4A, AAC, OGG).

## Architecture

### mix_fingerprint.py

Runs six sequential analyses on the full audio array loaded into memory via `librosa.load()`:

1. **Energy curve** — RMS per 10-second window, normalized 0–100
2. **Overall BPM + key** — `librosa.beat.beat_track` + `chroma_cqt` global mean
3. **Tempo tracking** — beat tracking in overlapping 60-second windows (50% overlap); only records BPM values in the 80–200 range to filter noise
4. **Key changes** — chroma dominant note per 30-second window; logs every shift
5. **Onset detection** — `librosa.onset.onset_detect` with `delta=0.07`, aggregated into 10-second density buckets
6. **Spectral brightness** — spectral centroid averaged in 30-second windows

All results are assembled into one dict and written as `mix_fingerprint.json`.

### transcribe_mix.py

Loads a Whisper model, calls `model.transcribe()` with `verbose=True` and `language="en"`, then writes each segment as `[MM:SS - MM:SS]  text` to `mix_transcript.txt`. The `MODEL` constant on line 26 controls model size (`tiny`/`base`/`small`/`medium`/`large`).

### Dependency auto-install pattern

Both scripts use a try/import → `subprocess pip install` fallback before importing heavy libraries. This means modifying imports requires updating both the try block and the install list.

## Output Schema

`mix_fingerprint.json` top-level keys: `file`, `duration_seconds`, `duration_label`, `overview`, `energy`, `tempo`, `keys`, `onsets`, `spectral`.

The `overview` object is the compact summary (BPM, key, tempo drift, key shift count, total onsets) and is the section most useful for LLM consumption without loading the full file.

## Runtime Expectations

CPU-only is slow. For a 60-minute mix: `mix_fingerprint.py` takes 10–20 minutes; `transcribe_mix.py` (small model) takes 45–90 minutes. GPU accelerates Whisper significantly. The `FP16 is not supported on CPU` Whisper warning is harmless.
