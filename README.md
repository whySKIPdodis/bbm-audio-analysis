# bbm-audio-analysis

Two Python scripts that pull a detailed audio fingerprint from any MP3 and generate a timestamped lyric transcript. Works on any mix, album, or audio file.

---

## Scripts

### `mix_fingerprint.py`
Runs six analyses on the audio file and outputs a single JSON:

- **Energy curve** — RMS energy normalized to 0-100 across the full duration, sampled every 10 seconds. Identifies peak and valley moments.
- **Overall BPM and key** — Global tempo estimate and dominant musical key.
- **Tempo tracking over time** — BPM measured in overlapping 60-second windows to detect drift or intentional tempo shifts across the mix.
- **Key changes over time** — Dominant key detected in 30-second windows, with a log of every shift.
- **Onset detection** — Every significant sound event across the full file. Aggregated into 10-second windows to find the densest transition zones.
- **Spectral brightness** — Average spectral centroid over time, showing how the tonal character of the mix changes.

Output: `mix_fingerprint.json`

---

### `transcribe_mix.py`
Runs OpenAI's Whisper model locally to generate a timestamped word-level transcript of the audio. Useful for mapping lyrics to exact timestamps, identifying songs in a mix, or building a song timeline.

Output: `mix_transcript.txt`

---

## Requirements

- Python 3.8 or higher
- ffmpeg installed and on your PATH

**Install ffmpeg on Windows:**
```
winget install ffmpeg
```

**Install ffmpeg on Mac:**
```
brew install ffmpeg
```

All Python dependencies (librosa, numpy, soundfile, openai-whisper, torch, etc.) install automatically on first run.

---

## Usage

1. Clone or download the repo
2. Put your audio file in the same folder as the script
3. Open the script and change line 8 to your filename:

```python
audio_file = "your_file.mp3"
```

4. Run from your terminal:

```
python mix_fingerprint.py
```

```
python transcribe_mix.py
```

First run of `transcribe_mix.py` downloads the Whisper model (~460MB for the default `small` setting). Subsequent runs skip the download.

---

## Whisper model options

In `transcribe_mix.py`, the model size is set on this line:

```python
MODEL = "small"
```

Options from fastest to most accurate: `tiny`, `base`, `small`, `medium`, `large`

`small` is a good balance for music. `medium` gives better lyric accuracy at roughly double the runtime. All models run locally — no API key or internet connection needed after the initial download.

---

## Runtime estimates

These are rough estimates on a modern CPU with 16GB+ RAM. A GPU will be significantly faster.

| File length | mix_fingerprint.py | transcribe_mix.py (small) |
|-------------|-------------------|--------------------------|
| 30 min | 5-10 min | 20-40 min |
| 60 min | 10-20 min | 45-90 min |
| 90 min | 15-30 min | 90-120 min |

---

## Output format

`mix_fingerprint.json` is structured as:

```
{
  "overview": { bpm, key, tempo drift, key shifts, total onsets },
  "energy":   { peak moments, low moments, full curve },
  "tempo":    { timeline of BPM over time },
  "keys":     { list of key changes, full timeline },
  "onsets":   { top transition zones, density timeline },
  "spectral": { brightness curve }
}
```

`mix_transcript.txt` is formatted as:

```
[MM:SS - MM:SS]  transcribed text
```

---

## Notes

- Both scripts work on any audio format ffmpeg supports: MP3, WAV, FLAC, M4A, AAC, OGG
- The `FP16 is not supported on CPU` warning from Whisper is harmless — it falls back to FP32 automatically
- Whisper is OpenAI's open source transcription model released under the MIT license. Running it locally is free with no usage limits.
