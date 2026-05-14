import os
from faster_whisper import WhisperModel

# Model config — "base" is fastest with good accuracy
# Change to "small" for better quality on powerful machines
MODEL_SIZE = os.environ.get("M78_MODEL", "base")

_model = None

def get_model():
    global _model
    if _model is None:
        print(f"[M-78] Loading Whisper model: {MODEL_SIZE}...")
        _model = WhisperModel(
            MODEL_SIZE,
            device="cpu",
            compute_type="int8",
            num_workers=2,           # parallel decode workers
            cpu_threads=4,           # use more CPU threads
        )
        print("[M-78] Model ready.")
    return _model


def transcribe(audio_path: str, language: str = "en") -> str:
    """
    Transcribe audio file and return raw text.
    Optimized for minimum latency:
      - beam_size=1 (greedy decode, fastest)
      - vad_filter=True (skip silent segments)
      - no word timestamps to reduce overhead
    """
    model = get_model()
    segments, _info = model.transcribe(
        audio_path,
        language=language,
        beam_size=1,                 # greedy — fastest
        best_of=1,
        temperature=0.0,             # deterministic
        vad_filter=True,             # skip silence
        vad_parameters=dict(
            min_silence_duration_ms=300,
            speech_pad_ms=100,
        ),
        word_timestamps=False,
        condition_on_previous_text=False,  # faster, no context build-up
    )

    parts = []
    for seg in segments:
        text = seg.text.strip()
        if text:
            parts.append(text)

    return " ".join(parts)
