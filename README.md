# Oracle CNE Model Training

Fine-tune Llama 3.1 8B on Oracle Cloud Native Environment (CNE) documentation using QLoRA on a local NVIDIA GPU.

## Table of Contents

- [Overview](#overview)
- [Hardware Requirements](#hardware-requirements)
- [Repository Structure](#repository-structure)
- [Setup](#setup)
- [Dataset](#dataset)
- [Dataset Generation](#dataset-generation)
- [Training](#training)
- [Model Outputs](#model-outputs)
- [Inference](#inference)
- [Deployment with Ollama](#deployment-with-ollama)
- [Troubleshooting](#troubleshooting)
- [Tuning Tips](#tuning-tips)
- [Resources](#resources)
- [License](#license)

## Overview

This project creates a specialized AI assistant for Oracle Cloud Native Environment:

- **285 curated Q&A pairs** covering CLI usage, cluster management, concepts, and quick start guides
- **4-bit QLoRA** training — ~9 GB peak VRAM, ~8 minutes to train on a 16 GB GPU
- **Local training script** (`train.py`) — no cloud services or proprietary libraries required
- **Multiple deployment options**: Python inference, Ollama, vLLM

## Hardware Requirements

| Component | Minimum    |
|-----------|------------|
| GPU VRAM  | 16 GB      |
| RAM       | 32 GB      |
| Disk      | 30 GB free |
| CUDA      | 12.1+      |

## Repository Structure

```
Dataset/
  ocne_training_data.jsonl           # 285 Q&A pairs in JSONL format
  ocne_cli_training_qa.md            # Source Q&A: CLI reference
  ocne_clusters_training_qa.md       # Source Q&A: cluster management
  ocne_concepts_training_qa.md       # Source Q&A: concepts guide
  ocne_quick_start_training_qa.md    # Source Q&A: quick start guide
  scrape_docs.py                     # Scrape Oracle CNE Release 2 docs → chunks JSON
  generate_qa.py                     # Generate Q&A pairs from chunks via local Ollama
  oracle_cne_unsloth_training.ipynb  # Legacy: original Colab notebook (deprecated)
train.py                             # Training script (local GPU)
inference.py                         # Inference script (CUDA / MPS / CPU)
convert_to_ollama.sh                 # Convert model to Ollama format
cleanup.sh                           # Remove large intermediate files after Ollama import
Modelfile                            # Ollama model configuration
requirements.txt                     # All dependencies (training, inference, dataset generation)
.env.example                         # Token configuration template
```

## Setup

### 1. Prerequisites

- NVIDIA GPU with 16 GB VRAM and CUDA toolkit installed — verify with `nvidia-smi` and `nvcc --version`
- Python 3.11+
- Hugging Face account with Llama 3.1 access:
  - Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) → New token → Role: Read
  - Accept the license at [meta-llama/Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)

### 2. Create environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate

# Install PyTorch with CUDA support
pip install torch --index-url https://download.pytorch.org/whl/cu126

# Install dependencies
pip install -r requirements.txt
```

> **Flash Attention 2 (optional):** `sdpa` (PyTorch built-in) is the default and works well.
> Only install `flash-attn` if your system CUDA toolkit version matches PyTorch's CUDA version:
> ```bash
> python -c "import torch; print(torch.version.cuda)"  # PyTorch CUDA version
> nvcc --version                                        # system toolkit version
> # If they match: pip install flash-attn --no-build-isolation
> ```

### 3. Configure Hugging Face token

```bash
cp .env.example .env
# Edit .env and replace hf_your_token_here with your actual token
```

## Dataset

The included training data (`Dataset/ocne_training_data.jsonl`) contains 285 hand-curated Q&A pairs covering four areas of Oracle CNE documentation:

- **CLI Reference** (`ocne_cli_training_qa.md`) — Command syntax, completion, environment variables, configuration
- **Cluster Management** (`ocne_clusters_training_qa.md`) — Provider types (libvirt, OCI, OLVM, BYO), scaling, updates
- **Concepts** (`ocne_concepts_training_qa.md`) — Architecture, components, OCK images, networking
- **Quick Start** (`ocne_quick_start_training_qa.md`) — Installation, first cluster creation, application deployment

These 285 pairs cover a useful subset of the docs, but more data generally means better fine-tuning. See [Dataset Generation](#dataset-generation) below to scrape all 9 sections of the Oracle CNE Release 2 docs and generate a much larger dataset automatically.

## Dataset Generation

Two scripts automate scraping the full Oracle CNE Release 2 documentation and generating Q&A pairs from it using a local Ollama model — no cloud API required.

### Prerequisites

- Ollama running locally (`ollama serve`) with a capable model pulled:
  ```bash
  ollama pull llama3.2
  ```
- Dataset generation packages are included in `requirements.txt` — no separate install needed.

### Step 1 — Scrape the docs

`Dataset/scrape_docs.py` crawls all 9 sections of the Oracle CNE Release 2 docs by following the sequential prev/next links on each page. It extracts page content, splits it by heading into text chunks, and saves them to `Dataset/ocne_chunks.json`.

The 9 sections scraped are: Release Notes, Concepts, Quick Start, CLI Reference, Cluster Management, Applications, Kubernetes, OCK Forge, and Upgrade.

```bash
python Dataset/scrape_docs.py --verbose
```

This takes ~5–10 minutes at the default 1-second polite delay between requests. Expect several hundred chunks covering every page of the docs.

Key options:
```
--sections   Comma-separated list of sections to scrape (default: all 9)
--delay      Seconds between requests (default: 1.0)
--min-chunk  Minimum characters to keep a chunk (default: 200)
--output     Output path (default: Dataset/ocne_chunks.json)
```

To scrape a single section for testing:
```bash
python Dataset/scrape_docs.py --sections concepts --verbose
```

### Step 2 — Generate Q&A pairs

`Dataset/generate_qa.py` reads the chunks, sends each one to a local Ollama model with a structured prompt, parses the `Q:` / `A:` formatted output, filters short or generic answers, deduplicates across all chunks, and writes a timestamped JSONL file.

```bash
# Sanity check: print the prompt for the first chunk and exit
python Dataset/generate_qa.py --dry-run

# Generate 3 pairs per chunk (recommended starting point)
python Dataset/generate_qa.py --pairs 3
```

Output is written to `Dataset/ocne_generated_YYYYMMDD_HHMMSS.jsonl` — a separate file so you can review before merging. Generation time depends on your GPU and model size (~20–60 min for the full chunk set).

Key options:
```
--model      Ollama model name (default: llama3.2:latest)
--pairs      Q&A pairs to request per chunk (default: 3)
--min-answer Minimum answer length in characters (default: 80)
--dry-run    Print prompt for first chunk and exit without calling Ollama
--chunks     Input chunks file (default: Dataset/ocne_chunks.json)
--output     Output JSONL path (default: auto-timestamped)
```

### Step 3 — Review and merge

The generated file is kept separate intentionally. Spot-check 10–20 pairs before merging:

```bash
# View first 20 pairs
head -20 Dataset/ocne_generated_*.jsonl

# Count how many were generated
wc -l Dataset/ocne_generated_*.jsonl

# Merge into the canonical training file when satisfied
cat Dataset/ocne_generated_*.jsonl >> Dataset/ocne_training_data.jsonl
```

The generated JSONL matches the existing format exactly (`{"instruction": "...", "response": "..."}`), so it drops straight into training without any conversion.

## Training

> **Stop Ollama before training** — it holds VRAM that training needs:
> ```bash
> sudo systemctl stop ollama
> ```

### Smoke test first

Verifies your setup end-to-end in ~30 seconds:

```bash
python train.py --epochs 1 --max-steps 20
```

Expected output: loss around 1.0–2.0, no OOM errors.

### Full training run

```bash
python train.py
```

| Parameter | Value |
|-----------|-------|
| Base model | Llama 3.1 8B Instruct |
| Method | QLoRA (4-bit NF4) |
| LoRA rank / alpha | 16 / 16 |
| Training samples | 285 (256 train / 29 validation) |
| Epochs | 10 |
| Effective batch size | 8 (batch 2 × grad accum 4) |
| Learning rate | 2e-4 |
| Max sequence length | 2048 tokens |
| Peak VRAM | ~9 GB |
| Training time | ~8 min on 16 GB GPU |
| Expected final loss | 0.35–0.45 |

### All CLI options

```
python train.py --help

  --base-model    HuggingFace model ID or local path
  --dataset       Path to JSONL file (default: Dataset/ocne_training_data.jsonl)
  --output-dir    Where to save LoRA adapters (default: Model/oracle_cne_lora)
  --epochs        Training epochs (default: 10)
  --batch-size    Per-device batch size (default: 2)
  --grad-accum    Gradient accumulation steps (default: 4, effective batch=8)
  --lr            Learning rate (default: 2e-4)
  --lora-rank     LoRA rank r (default: 16)
  --lora-alpha    LoRA alpha (default: 16)
  --max-seq-len   Max token length (default: 2048)
  --max-steps     Override epochs with a fixed step count
  --merge         Merge LoRA into base model after training (saves ~14 GB 16-bit model)
  --flash-attn    Use flash_attention_2 instead of sdpa (requires flash-attn package)
```

### Monitoring training

Training logs to stdout. Key lines to watch:

```
{'loss': 1.85, 'epoch': 0.1}   ← early loss (expected: 1.5–2.5)
{'loss': 0.85, 'epoch': 1.0}   ← after epoch 1 (expected: 0.7–1.2)
{'loss': 0.42, 'epoch': 3.0}   ← final (target: 0.3–0.5)
```

Eval loss is logged every 25 steps. If eval loss is significantly higher than train loss (>0.3 gap), the model may be overfitting — reduce epochs or increase dropout.

## Model Outputs

After training, LoRA adapters are saved to `Model/oracle_cne_lora/`:

```
Model/oracle_cne_lora/
  adapter_config.json
  adapter_model.safetensors   (~100–200 MB)
  tokenizer.json
  tokenizer_config.json
  special_tokens_map.json
```

To also produce a standalone merged model:

```bash
python train.py --merge
```

This saves the weights as 16-bit safetensors to `Model/oracle_cne_merged_16bit/` (~14 GB on disk).

> **16-bit on disk, 4-bit in VRAM:** The merged model is stored at full float16 precision so it can be cleanly exported to GGUF (re-quantizing an already-quantized model degrades quality). At inference time on CUDA, `inference.py` re-quantizes the weights to 4-bit using bitsandbytes, reducing VRAM usage from ~15 GB to ~5 GB.

Model files are not committed to this repository.

## Inference

### Python inference

```bash
# Interactive mode
python inference.py

# Single question
python inference.py --question "How do I create a cluster with ocne?"
```

The script auto-detects CUDA → MPS → CPU. On CUDA the model is loaded in 4-bit quantization (~5 GB VRAM), which fits comfortably on a 16 GB GPU.

### Using LoRA adapters directly

Load adapters on top of the base model in your own script:

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")
model = PeftModel.from_pretrained(base, "Model/oracle_cne_lora")
tokenizer = AutoTokenizer.from_pretrained("Model/oracle_cne_lora")
```

## Deployment with Ollama

### Step 1 — Export to GGUF

Use a **separate venv** for llama.cpp — its dependencies should not be mixed with the training stack.

```bash
# Clone llama.cpp once alongside the project
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Build llama-quantize
cmake -B build && cmake --build build --config Release -j$(nproc)

# Create a dedicated venv for llama.cpp
python3 -m venv venv-llamacpp
source venv-llamacpp/bin/activate
pip install -r requirements.txt

# Convert merged model to f16 GGUF
python3 convert_hf_to_gguf.py ../ocne-model-training/Model/oracle_cne_merged_16bit \
  --outfile ../ocne-model-training/Model/oracle_cne_f16.gguf \
  --outtype f16

# Quantize to Q4_K_M
./build/bin/llama-quantize \
  ../ocne-model-training/Model/oracle_cne_f16.gguf \
  ../ocne-model-training/Model/oracle_cne_q4_k_m.gguf \
  Q4_K_M

# Remove the intermediate f16 file (~15 GB)
rm ../ocne-model-training/Model/oracle_cne_f16.gguf

deactivate
```

### Step 2 — Import into Ollama

```bash
cd ../ocne-model-training
bash convert_to_ollama.sh
ollama run oracle-cne
```

### Step 3 — Cleanup

After the model is imported into Ollama, free ~22 GB of intermediate files while keeping everything needed to retrain:

```bash
bash cleanup.sh
```

This removes the merged 16-bit model, GGUF files, training checkpoints, and the llama.cpp build and venv. It keeps `venv/`, `Model/oracle_cne_lora/`, `Dataset/`, and `~/.cache/huggingface`.

## Troubleshooting

### CUDA out of memory during training

**Check Ollama is stopped.** Ollama keeps models loaded in VRAM — stop it before training:
```bash
sudo systemctl stop ollama
```
Verify with `nvidia-smi` that only desktop processes (Xorg, gnome-shell) are using the GPU.

**Check transformers version.** transformers 5.x introduced a new model loading path that loads weights in full precision before quantizing, consuming ~15 GB instead of ~5 GB and causing OOM on 16 GB GPUs. Requirements pin `transformers<5.0` to prevent this. If you see OOM at ~98% of weight loading:
```bash
pip show transformers | grep Version
# If 5.x: pip install "transformers>=4.47,<5.0"
```

**If VRAM is clear and transformers is 4.x**, reduce sequence length:
```bash
python train.py --max-seq-len 1024
```

### Flash Attention 2 compile error

Training defaults to `sdpa` (PyTorch built-in), which also uses Flash Attention kernels automatically. Only use `--flash-attn` if you have the `flash-attn` package installed.

`flash-attn` requires the system CUDA toolkit version to match what PyTorch was built against. Check with:
```bash
python -c "import torch; print(torch.version.cuda)"  # PyTorch CUDA version
nvcc --version                                        # system toolkit version
```
If they differ, use the default `sdpa`.

### Model not found during training

The base model downloads automatically from Hugging Face on first run (~16 GB). Make sure you have accepted the Llama 3.1 license and your `.env` token is correct:
```bash
huggingface-cli whoami
```

### Training loss not decreasing

- Try increasing LoRA rank: `--lora-rank 32`
- Try more epochs: `--epochs 15`
- Check `Dataset/ocne_training_data.jsonl` for duplicate or malformed entries

### Slow training despite GPU

Confirm the GPU is being used:
```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

## Tuning Tips

| Goal | Change |
|------|--------|
| Better quality | Increase `--lora-rank` to 32 or 64 |
| Faster training | Reduce `--max-seq-len` to 1024 |
| Prevent overfitting | Reduce `--epochs` to 2 |
| More stable training | Reduce `--lr` to 1e-4 |
| More creative responses | Increase temperature in `inference.py` |

## Resources

- [Llama 3.1 on Hugging Face](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)
- [PEFT documentation](https://huggingface.co/docs/peft)
- [TRL SFTTrainer documentation](https://huggingface.co/docs/trl/sft_trainer)
- [BitsAndBytes (QLoRA)](https://github.com/TimDettmers/bitsandbytes)
- [Flash Attention 2](https://github.com/Dao-AILab/flash-attention)
- [Oracle CNE documentation](https://docs.oracle.com/en/operating-systems/olcne/)

## License

MIT License. See [LICENSE](LICENSE) for details.

Note: Usage of the fine-tuned model is subject to the [Llama 3.1 license](https://llama.meta.com/llama3_1/license/) and Oracle documentation usage policies.
