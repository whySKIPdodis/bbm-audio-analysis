import subprocess
import sys
import os

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

print("Installing dependencies...")
try:
    import whisper
except ImportError:
    print("Installing openai-whisper (this may take a few minutes)...")
    install("openai-whisper")
    install("ffmpeg-python")
    import whisper

# ---- CHANGE THIS to your MP3 path ----
audio_file = "Two Friends Big Bootie Mix, Vol. 27.mp3"
# --------------------------------------

output_file = "mix_transcript.txt"

# Model options (from fastest/least accurate to slowest/most accurate):
# "tiny", "base", "small", "medium", "large"
# "small" is a good balance for a music mix - catches most lyrics without taking forever
MODEL = "small"

print(f"Loading Whisper model: {MODEL}")
print("First run will download the model (~460MB for small). Subsequent runs are instant.")
model = whisper.load_model(MODEL)

print(f"\nTranscribing: {audio_file}")
print("This will take a while for a 67 minute mix. Go make a coffee.")
print("Progress will show below...\n")

result = model.transcribe(
    audio_file,
    verbose=True,          # shows progress segment by segment
    language="en",         # force English, speeds things up
    task="transcribe",
    word_timestamps=False  # segment-level timestamps are enough
)

print(f"\nWriting transcript to {output_file}...")

with open(output_file, "w", encoding="utf-8") as f:
    f.write(f"Whisper transcript: {audio_file}\n")
    f.write(f"Model: {MODEL}\n")
    f.write("=" * 60 + "\n\n")

    for segment in result["segments"]:
        start = segment["start"]
        end = segment["end"]
        text = segment["text"].strip()

        # Format timestamps as MM:SS
        start_label = f"{int(start // 60)}:{int(start % 60):02d}"
        end_label = f"{int(end // 60)}:{int(end % 60):02d}"

        f.write(f"[{start_label} - {end_label}]  {text}\n")

print(f"\nDone! Transcript saved to: {output_file}")
print(f"Total segments: {len(result['segments'])}")
print(f"\nUpload '{output_file}' to Claude for song mapping.")
