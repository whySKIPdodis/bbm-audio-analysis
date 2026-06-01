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
Runs OpenAI's Whisper model locally to generate a timestamped transcript of the audio. Useful for mapping lyrics to exact timestamps, identifying songs in a mix, or building a song timeline.

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
|-------------|-------------------|--------------------------:|
| 30 min      | 5-10 min          | 20-40 min                 |
| 60 min      | 10-20 min         | 45-90 min                 |
| 90 min      | 15-30 min         | 90-120 min                |

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

## Interpreting the output

### mix_fingerprint.json

**Energy curve** — look at `energy_normalized` over time. Values above 80 are peak moments, below 35 are breakdowns or transitions. The gap between your highest and lowest points tells you how dynamic the mix is. A mix that stays between 60-80 the whole time is less interesting than one that swings between 25 and 100.

**Tempo drift** — compare `tempo_start_avg_bpm` vs `tempo_end_avg_bpm` in the overview. A positive drift means the mix speeds up. Even a few BPM over an hour is intentional if it's consistent. Negative drift is rare and usually means the DJ is winding down.

**Key changes** — 90 shifts in 67 minutes is high. 20-30 would be more typical for a mix that stays in a harmonic pocket. High shift counts mean the DJ is prioritizing energy and surprise over harmonic smoothness. Neither is wrong, just different approaches.

**Top transition zones** — the `onsets_per_10sec` values in `top_transition_zones` show where the most is happening at once. High numbers (40+) mean dense layering, drops, or fast edits. Compare these timestamps against your energy curve to see if busy transitions correlate with energy peaks or serve as the mechanism to get there.

**Spectral brightness** — higher `brightness_hz` values mean the mix is tonally brighter (more high-frequency content, think synths and hi-hats dominant). Lower values mean heavier, bassier sections. A brightness dip that matches an energy dip is a double-down on a breakdown. A brightness spike without an energy spike might be a filter sweep or transition effect.

---

### mix_transcript.txt

The transcript works best when you treat it as a search tool rather than reading it top to bottom. Search for a lyric you remember and you get the timestamp. From there you can cross-reference that timestamp against the energy JSON to see what was happening sonically at that moment.

Whisper mishears things, especially when vocals are heavily processed or buried in a mix. If a section looks like gibberish, the audio is probably instrumental or the vocals are too distorted to transcribe cleanly. That's useful information too — it tells you where the DJ stripped back to pure sound.

---

## How to use this without an LLM

The JSON files are plain text and work with anything that can read JSON.

**Spreadsheets** — paste the energy curve data into Excel or Google Sheets and chart it. You get a visual energy map of your mix in about two minutes.

**Any LLM** — upload the JSON to ChatGPT, Claude, Gemini, or similar and ask it to interpret the results. The structured format is readable by any model. Uploading the transcript alongside the JSON lets the model map lyrics to energy moments.

**Python / pandas** — load the JSON directly and do your own analysis. Filter for moments above a certain energy threshold, calculate rolling averages, compare two mixes against each other.

**Comparing mixes** — run multiple files through `mix_fingerprint.py` and compare the overview sections side by side. BPM drift, key shift count, peak energy timing, and onset density give you a quick fingerprint of each DJ's style.

**DJs specifically** — the tempo timeline is useful for understanding your own sets. If your BPM tracking shows inconsistency where you expected locked tempo, you'll see it in the data. The onset density timeline can also help identify transitions that felt busier or cleaner than intended.

---

## Notes

- Both scripts work on any audio format ffmpeg supports: MP3, WAV, FLAC, M4A, AAC, OGG
- The `FP16 is not supported on CPU` warning from Whisper is harmless — it falls back to FP32 automatically
- Whisper is OpenAI's open source transcription model released under the MIT license. Running it locally is free with no usage limits
