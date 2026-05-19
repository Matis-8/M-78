import os
from faster_whisper import WhisperModel

def download():
    model_size = "base"
    dest_dir = os.path.join("assets", "models", f"whisper-{model_size}")
    os.makedirs(dest_dir, exist_ok=True)
    
    print(f"Downloading '{model_size}' model to {dest_dir}...")
    # This will download and cache the model, then we can copy it or redirect downloader
    # Faster-whisper actually uses the 'huggingface_hub' to download.
    # We can use the 'download_model' method from faster_whisper to get the path.
    from faster_whisper.utils import download_model
    
    model_path = download_model(model_size, output_dir=dest_dir)
    print(f"Model downloaded to: {model_path}")

if __name__ == "__main__":
    download()
