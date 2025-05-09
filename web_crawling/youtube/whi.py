import whisper
from pyannote.audio import Pipeline
from pyannote_whisper.utils import diarize_text
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization",
                                    use_auth_token="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")
model = whisper.load_model("tiny.en")
asr_result = model.transcribe("dc.webm")
diarization_result = pipeline("dc.webm")
final_result = diarize_text(asr_result, diarization_result)

for seg, spk, sent in final_result:
    line = f'{seg.start:.2f} {seg.end:.2f} {spk} {sent}'
    print(line)