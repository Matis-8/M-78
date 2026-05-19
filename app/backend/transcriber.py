import os
from faster_whisper import WhisperModel
from app.utils.logger import log, log_error

# Model config — "base" is fastest with good accuracy
# Change to "small" for better quality on powerful machines
MODEL_SIZE = os.environ.get("M78_MODEL", "base")

_model = None

def get_model():
    global _model
    if _model is None:
        # 1. Determine base path (MEIPASS for bundle, CWD for dev)
        import sys
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        # 2. Check for VAD assets
        vad_path = os.path.join(base, "faster_whisper", "assets", "silero_vad_v6.onnx")
        if os.path.exists(vad_path):
            log(f"VAD model asset verified at: {vad_path}", role="Backend")
        else:
            log_error(f"VAD model asset MISSING at: {vad_path}", role="Backend")

        # 3. Determine Model Path (Bundle first, then dev local, then cache)
        local_model_path = os.path.join(base, "assets", "models", f"whisper-{MODEL_SIZE}")
        
        if os.path.exists(local_model_path):
            log(f"Loading local bundled model from: {local_model_path}", role="Backend")
            model_to_load = local_model_path
        else:
            log(f"Local model not found. Falling back to default loader for {MODEL_SIZE}...", role="Backend")
            model_to_load = MODEL_SIZE

        log(f"Initializing Whisper model...", role="Backend")
        _model = WhisperModel(
            model_to_load,
            device="cpu",
            compute_type="int8",
            num_workers=2,           # parallel decode workers
            cpu_threads=4,           # use more CPU threads
        )
        log("[M-78] Model ready.", role="Backend")
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
