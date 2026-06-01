import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

print("Checking dependencies...")
for pkg in ["librosa", "numpy", "soundfile"]:
    try:
        __import__(pkg)
    except ImportError:
        print(f"Installing {pkg}...")
        install(pkg)

import json
import numpy as np
import librosa

# ---- CHANGE THIS to your MP3 filename ----
audio_file = "your_mix.mp3"
# ------------------------------------------

output_file = "mix_fingerprint.json"

print(f"\nLoading: {audio_file}")
print("This takes a few minutes for a long mix. Hang tight.\n")

y, sr = librosa.load(audio_file, mono=True)
duration = librosa.get_duration(y=y, sr=sr)
print(f"Duration: {int(duration//60)}:{int(duration%60):02d}\n")


# ─── 1. ENERGY CURVE ──────────────────────────────────────────────────────────
print("[1/6] Energy curve...")
hop_length = sr * 10
rms = librosa.feature.rms(y=y, frame_length=hop_length * 2, hop_length=hop_length)[0]
energy_curve = []
for i, val in enumerate(rms):
    t = i * 10
    if t <= duration:
        energy_curve.append({
            "time_seconds": t,
            "time_label": f"{int(t//60)}:{int(t%60):02d}",
            "energy": round(float(val), 5)
        })

max_e = max(e["energy"] for e in energy_curve) or 1
for e in energy_curve:
    e["energy_normalized"] = round((e["energy"] / max_e) * 100, 1)

peak_moments = sorted(
    sorted(energy_curve, key=lambda x: x["energy_normalized"], reverse=True)[:10],
    key=lambda x: x["time_seconds"]
)
low_moments = sorted(
    sorted(energy_curve, key=lambda x: x["energy_normalized"])[:5],
    key=lambda x: x["time_seconds"]
)


# ─── 2. OVERALL BPM + KEY ─────────────────────────────────────────────────────
print("[2/6] Overall BPM and key...")
tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
overall_bpm = round(float(np.atleast_1d(tempo)[0]), 1)

chroma_full = librosa.feature.chroma_cqt(y=y, sr=sr)
key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
overall_key = key_names[int(np.argmax(chroma_full.mean(axis=1)))]

avg_contrast = round(float(np.mean(librosa.feature.spectral_contrast(y=y, sr=sr))), 3)


# ─── 3. TEMPO TRACKING OVER TIME ──────────────────────────────────────────────
print("[3/6] Tempo tracking over time...")
tempo_window = 60
samples_per_window = sr * tempo_window
tempo_timeline = []

for start_sample in range(0, len(y) - samples_per_window, samples_per_window // 2):
    segment = y[start_sample:start_sample + samples_per_window]
    t = start_sample / sr
    try:
        seg_tempo, _ = librosa.beat.beat_track(y=segment, sr=sr)
        bpm = float(np.atleast_1d(seg_tempo)[0])
        if 80 < bpm < 200:
            tempo_timeline.append({
                "time_seconds": round(t, 1),
                "time_label": f"{int(t//60)}:{int(t%60):02d}",
                "bpm": round(bpm, 1)
            })
    except:
        pass

bpms = [x["bpm"] for x in tempo_timeline] if tempo_timeline else [overall_bpm]
tempo_start_avg = round(float(np.mean(bpms[:5])), 1)
tempo_end_avg = round(float(np.mean(bpms[-5:])), 1)
tempo_drift = round(tempo_end_avg - tempo_start_avg, 1)


# ─── 4. CHROMA / KEY CHANGES OVER TIME ────────────────────────────────────────
print("[4/6] Key changes over time...")
window_size = 30
hop_length_chroma = 512
chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length_chroma)
frames_per_sec = sr / hop_length_chroma

chroma_timeline = []
key_changes = []
prev_key = None

for t in range(0, int(duration), window_size):
    start_frame = int(t * frames_per_sec)
    end_frame = min(int((t + window_size) * frames_per_sec), chroma.shape[1])
    if start_frame >= chroma.shape[1]:
        break

    window_chroma = chroma[:, start_frame:end_frame].mean(axis=1)
    dominant_idx = int(np.argmax(window_chroma))
    dominant_key = key_names[dominant_idx]
    strength = round(float(window_chroma[dominant_idx] / window_chroma.sum()), 3)
    changed = prev_key is not None and dominant_key != prev_key

    chroma_timeline.append({
        "time_seconds": t,
        "time_label": f"{t//60}:{t%60:02d}",
        "key": dominant_key,
        "key_strength": strength,
        "key_changed": changed
    })

    if changed:
        key_changes.append({
            "time_seconds": t,
            "time_label": f"{t//60}:{t%60:02d}",
            "from_key": prev_key,
            "to_key": dominant_key
        })

    prev_key = dominant_key


# ─── 5. ONSET DETECTION ───────────────────────────────────────────────────────
print("[5/6] Onset detection...")
onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units='frames', backtrack=True, delta=0.07)
onset_times = librosa.frames_to_time(onset_frames, sr=sr)

onset_density = []
for t in range(0, int(duration), 10):
    count = int(np.sum((onset_times >= t) & (onset_times < t + 10)))
    onset_density.append({
        "time_seconds": t,
        "time_label": f"{t//60}:{t%60:02d}",
        "onsets_per_10sec": count
    })

top_transition_zones = sorted(
    sorted(onset_density, key=lambda x: x["onsets_per_10sec"], reverse=True)[:20],
    key=lambda x: x["time_seconds"]
)


# ─── 6. SPECTRAL SUMMARY ──────────────────────────────────────────────────────
print("[6/6] Spectral summary...")
spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
brightness_curve = []
window_frames = int(sr * 30 / 512)
for i in range(0, len(spectral_centroid) - window_frames, window_frames):
    t = int(i * 512 / sr)
    avg_centroid = float(np.mean(spectral_centroid[i:i+window_frames]))
    brightness_curve.append({
        "time_seconds": t,
        "time_label": f"{t//60}:{t%60:02d}",
        "brightness_hz": round(avg_centroid, 1)
    })


# ─── SAVE ─────────────────────────────────────────────────────────────────────
result = {
    "file": audio_file,
    "duration_seconds": round(duration, 1),
    "duration_label": f"{int(duration//60)}:{int(duration%60):02d}",

    "overview": {
        "overall_bpm": overall_bpm,
        "overall_key": overall_key,
        "avg_spectral_contrast": avg_contrast,
        "tempo_start_avg_bpm": tempo_start_avg,
        "tempo_end_avg_bpm": tempo_end_avg,
        "tempo_drift_bpm": tempo_drift,
        "total_key_shifts": len(key_changes),
        "total_onsets": len(onset_times)
    },

    "energy": {
        "peak_moments": peak_moments,
        "low_moments": low_moments,
        "full_curve": energy_curve
    },

    "tempo": {
        "timeline": tempo_timeline
    },

    "keys": {
        "changes": key_changes,
        "timeline": chroma_timeline
    },

    "onsets": {
        "top_transition_zones": top_transition_zones,
        "density_timeline": onset_density
    },

    "spectral": {
        "brightness_curve": brightness_curve
    }
}

with open(output_file, "w") as f:
    json.dump(result, f, indent=2)

print(f"\nDone. Saved to: {output_file}")
print(f"\nOverview:")
print(f"  Duration:     {int(duration//60)}:{int(duration%60):02d}")
print(f"  Overall BPM:  {overall_bpm}")
print(f"  Overall key:  {overall_key}")
print(f"  Tempo drift:  {tempo_drift:+.1f} BPM ({tempo_start_avg} -> {tempo_end_avg})")
print(f"  Key shifts:   {len(key_changes)}")
print(f"  Onsets:       {len(onset_times):,}")
