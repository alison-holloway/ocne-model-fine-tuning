# Oracle CNE Model Training

Fine-tune Llama 3.1 8B on Oracle Cloud Native Environment (CNE) documentation using QLoRA on a local NVIDIA GPU.

## Table of Contents

- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [Quick Start](#quick-start)
- [Training Details](#training-details)
- [Dataset](#dataset)
- [Dataset Generation](#dataset-generation)
- [Model Outputs](#model-outputs)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [License](#license)

## Overview

This project creates a specialized AI assistant for Oracle Cloud Native Environment:

- **285 curated Q&A pairs** covering CLI usage, cluster management, concepts, and quick start guides
- **4-bit QLoRA** training — ~9 GB peak RAM, ~8 minutes to train on a 16 GB GPU
- **Local training script** (`train.py`) — no cloud services or proprietary libraries required
- **Multiple deployment options**: Python inference, Ollama, vLLM

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
requirements.txt                     # Inference dependencies
requirements-training.txt            # Training dependencies
requirements-datagen.txt             # Dataset generation dependencies
.env.example                         # Token configuration template
plan.md                              # Detailed training guide and troubleshooting
```

## Quick Start

### 1. Prerequisites

- NVIDIA GPU with 16 GB VRAM
- 32 GB system RAM
- CUDA toolkit installed (`nvidia-smi` and `nvcc --version` should both work)
- Hugging Face account with [Llama 3.1 access](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)

### 2. Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cu126
pip install -r requirements-training.txt

cp .env.example .env
# Edit .env and add your Hugging Face token
```

### 3. Train

```bash
# Smoke test first (~30 sec)
python train.py --epochs 1 --max-steps 20

# Full training run (~8 min)
python train.py
```

### 4. Run inference

```bash
python inference.py --question "How do I create a cluster with ocne?"
```

## Training Details

| Parameter | Value |
|-----------|-------|
| Base model | Llama 3.1 8B Instruct |
| Method | QLoRA (4-bit NF4) |
| LoRA rank / alpha | 16 / 16 |
| Training samples | 285 (256 train / 29 validation) |
| Epochs | 10 |
| Effective batch size | 8 (batch 2 × grad accum 4) |
| Peak RAM | ~9 GB |
| Training time | ~8 min on 16 GB GPU |
| Expected final loss | 0.35–0.45 |

## Dataset

The training data covers four areas of Oracle CNE documentation:

- **CLI Reference** - Command syntax, completion, environment variables, configuration
- **Cluster Management** - Provider types (libvirt, OCI, OLVM, BYO), scaling, updates
- **Concepts** - Architecture, components, OCK images, networking
- **Quick Start** - Installation, first cluster creation, application deployment

## Dataset Generation

To generate a larger dataset from the full Oracle CNE Release 2 documentation using a local Ollama model:

```bash
pip install -r requirements-datagen.txt

# Step 1: Scrape the docs (~5-10 min)
python Dataset/scrape_docs.py --verbose

# Step 2: Sanity check the prompt
python Dataset/generate_qa.py --dry-run

# Step 3: Generate Q&A pairs (~20-60 min depending on GPU)
python Dataset/generate_qa.py --pairs 3

# Step 4: Review the output, then merge when satisfied
cat Dataset/ocne_generated_*.jsonl >> Dataset/ocne_training_data.jsonl
```

Requires a running Ollama instance with `llama32:latest` (or pass `--model` to use another).
See [plan.md](plan.md) for full details and CLI options.

## Model Outputs

After training:
- **LoRA adapters** (`Model/oracle_cne_lora/`, ~100–200 MB) — lightweight, requires base Llama 3.1 8B
- **Merged 16-bit model** (`Model/oracle_cne_merged_16bit/`, ~14 GB on disk, optional) — the LoRA weights baked into the base model and saved as float16 safetensors. Used as the source for inference and GGUF export.

To produce the merged model: `python train.py --merge`

> **16-bit on disk, 4-bit in VRAM:** The merged model is stored at full float16 precision so it can be cleanly exported to GGUF (re-quantizing an already-quantized model degrades quality). At inference time on CUDA, `inference.py` re-quantizes the weights to 4-bit using bitsandbytes, reducing VRAM usage from ~15 GB to ~5 GB.

Model files are not committed to this repository. See [plan.md](plan.md) for full deployment instructions.

## Deployment

### Local Inference (Python)

```bash
pip install -r requirements.txt

# Interactive mode
python inference.py

# Single question
python inference.py --question "How do I create a cluster with ocne?"
```

On CUDA, the 16-bit weights are loaded from disk and re-quantized to 4-bit in VRAM (~5 GB). Auto-detects CUDA → MPS → CPU.

### Ollama

```bash
# Export GGUF first (see plan.md for llama.cpp instructions)
bash convert_to_ollama.sh
ollama run oracle-cne
```

### Cleanup

After the model is imported into Ollama, remove large intermediate files (~22 GB) while keeping everything needed to retrain:

```bash
bash cleanup.sh
```

## Documentation

See [plan.md](plan.md) for the complete guide including:
- Full setup and install steps
- All `train.py` CLI flags
- Hyperparameter tuning advice
- Troubleshooting (OOM, flash-attn version mismatch, slow training)
- Ollama and vLLM deployment

## License

MIT License. See [LICENSE](LICENSE) for details.

Note: Usage of the fine-tuned model is subject to the [Llama 3.1 license](https://llama.meta.com/llama3_1/license/) and Oracle documentation usage policies.
