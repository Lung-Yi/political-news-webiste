from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
from pydub import AudioSegment
import tempfile
import os

# === 設定路徑與模型 ===
audio_path = "dc.webm"
output_path = "transcription.txt"
model_size = "large-v3"
hf_token = "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"  # 請填入你的 Hugging Face token

# === Step 1: Whisper 語音轉文字（取得 segments + timestamps） ===
# model = WhisperModel(model_size, device="cuda", compute_type="float16")
model = WhisperModel(model_size, device="cpu", compute_type="default")


segments, info = model.transcribe(audio_path, beam_size=5)

# 暫存語音切片
audio = AudioSegment.from_file(audio_path)

# === Step 2: Pyannote 說話人分離 ===
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=hf_token)
diarization = pipeline(audio_path)

# === Step 3: 合併 Whisper 語句與 Speaker 標籤 ===
# 將 diarization segment (start, end, speaker) 存成 list
speaker_segments = []
for turn in diarization.itertracks(yield_label=True):
    start = turn[0].start
    end = turn[0].end
    speaker = turn[2]
    speaker_segments.append((start, end, speaker))

def match_speaker(start, end):
    for seg_start, seg_end, speaker in speaker_segments:
        if seg_start <= start <= seg_end or seg_start <= end <= seg_end:
            return speaker
    return "Unknown"

# === Step 4: 寫入純文字輸出（無時間戳） ===
with open(output_path, "w", encoding="utf-8") as f:
    for segment in segments:
        speaker = match_speaker(segment.start, segment.end)
        text_line = f"{speaker}: {segment.text.strip()}"
        print(text_line)
        f.write(text_line + "\n")

print(f"\n 完成！結果已儲存於 {output_path}")
