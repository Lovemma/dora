# Dora Model Manager

`download_models.py` is a universal downloader for Hugging Face models plus curated shortcuts for Dora voice pipelines (FunASR, PrimeSpeech, Kokoro, Qwen MLX, etc.). This README consolidates the quick start and detailed usage notes into one place, including the latest Kokoro features.

---

## 1. Installation

If you have not yet provisioned a Dora development environment, follow `examples/setup-new-chat/README.md` first (it installs `uv`, `rustup`, base Python tooling, etc.).

Inside this directory the model manager installs extra Python packages lazily, but you can pre-install them:

```bash
pip install huggingface-hub tqdm
```

The FunASR shortcuts rely on ModelScope; the setup instructions in `setup-new-chat` already cover the required runtime, so no separate `setup.sh` invocation is necessary.

---

## 2. Quick Start

All commands below assume you are in `examples/model-manager/`.

### List cached models

```bash
python download_models.py --list
```

Scans `~/.cache/huggingface/hub/` and `~/.dora/models/` (PrimeSpeech/Kokoro/FunASR) and prints sizes plus file counts.

### Typical downloads

```bash
# ASR models (FunASR Paraformer + punctuation)
python download_models.py --download funasr

# PrimeSpeech base (Chinese HuBERT & RoBERTa) + all voices
python download_models.py --download primespeech

# Kokoro base + all voices (config.json, kokoro-v1_0.pth, voices/*.pt)
python download_models.py --download kokoro

# Qwen3 MLX (choose one)
python download_models.py --download Qwen/Qwen3-8B-MLX-4bit
```

### Removing artefacts

```bash
python download_models.py --remove funasr
python download_models.py --remove primespeech-base
python download_models.py --remove all-voices
python download_models.py --remove kokoro        # base + voices + HF cache
```

---

## 3. Full Command Reference

### 3.1 Hugging Face repositories

```bash
# Download entire repo snapshot
python download_models.py --download mlx-community/gemma-3-12b-it-4bit

# Custom cache directory
python download_models.py --download meta-llama/Llama-2-7b-hf --hf-dir ~/llama-cache

# Select file types only
python download_models.py --download mlx-community/gemma-3-12b-it-4bit --patterns "*.safetensors" "*.json"

# Specific revision
python download_models.py --download openai/whisper-large-v3 --revision main

# Remove cached repo
python download_models.py --remove mlx-community/gemma-3-12b-it-4bit
```

### 3.2 FunASR

```bash
python download_models.py --download funasr
python download_models.py --remove funasr
```

Content lands in `~/.dora/models/asr/funasr` by default.

### 3.3 PrimeSpeech

```bash
# Base models only
python download_models.py --download primespeech-base

# List available voices
python download_models.py --list-voices

# All voices
python download_models.py --voice all

# Specific voice
python download_models.py --voice "Luo Xiang"

# Removal
python download_models.py --remove "Luo Xiang"
python download_models.py --remove all-voices
python download_models.py --remove primespeech-base
```

PrimeSpeech assets are stored under `~/.dora/models/primespeech` unless you pass `--models-dir`.

### 3.4 Kokoro

```bash
# Base files (config.json + kokoro-v1_0.pth) and cache refresh
python download_models.py --download kokoro-base

# All voices only
python download_models.py --download kokoro-voices

# Both base and voices
python download_models.py --download kokoro

# Specific voice (comma-separated list allowed)
python download_models.py --kokoro-voice af_heart

# List available voices on Hugging Face
python download_models.py --list-kokoro-voices

# Remove
python download_models.py --remove kokoro-base
python download_models.py --remove kokoro-voices
python download_models.py --remove kokoro
```

Kokoro base files and voices are placed under `~/.dora/models/kokoro`. The script also mirrors the `hexgrad/Kokoro-82M` snapshot in your HF cache; removal cleans both local files and cached snapshot.

### 3.5 Other shortcuts

The script recognises many common repos used in Dora voice demos. Examples:

```bash
python download_models.py --download openai/whisper-base
python download_models.py --download Qwen/Qwen3-14B-MLX-4bit
python download_models.py --download mlx-community/gemma-2-9b-it-4bit
```

Run `python download_models.py --help` for the full option list.

---

## 4. Storage Layout

| Location | Contents |
|----------|----------|
| `~/.cache/huggingface/hub/` | Hugging Face snapshots (e.g. `hexgrad--Kokoro-82M`) |
| `~/.dora/models/primespeech/` | PrimeSpeech base + voices |
| `~/.dora/models/kokoro/` | Kokoro base + voices |
| `~/.dora/models/asr/funasr/` | FunASR ASR models |

Override with `--hf-dir`, `--models-dir`, or `--kokoro-dir` when necessary.

---

## 5. Troubleshooting

- **“Model not found”** – ensure the repo ID is correct (case-sensitive). Use `--list` to confirm downloads.
- **Permission errors** – use a user-writable path via `--hf-dir` / `--models-dir`, or adjust filesystem permissions.
- **Interrupted downloads** – the script uses `resume_download=True`; re-run the same command to continue.
- **PrimeSpeech warning** – even if `dora-primespeech` isn’t installed, you can still fetch the models; install the node before running the TTS pipeline.

---

## 6. File Overview

- `download_models.py` – main CLI
- `download_all_models.sh` – convenience script for bulk downloads

Use this tool to keep Dora voice demos stocked with the correct ASR, LLM, and TTS assets—especially PrimeSpeech and Kokoro, which rely on precise directory structures.
