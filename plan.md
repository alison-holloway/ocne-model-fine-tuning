# OCNE Model Training — Local GPU Guide

Fine-tunes Llama 3.1 8B on Oracle CNE documentation using QLoRA on a local NVIDIA GPU.
No cloud service or Unsloth required.

## Table of Contents

- [Hardware Requirements](#hardware-requirements)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Training](#training)
  - [Smoke test first](#smoke-test-first-verifies-setup-2-min)
  - [Full training run](#full-training-run)
  - [All CLI options](#all-cli-options)
- [Output Files](#output-files)
- [Monitoring Training](#monitoring-training)
- [Inference](#inference)
  - [Using the merged 16-bit model](#using-the-merged-16-bit-model)
  - [Using LoRA adapters directly](#using-lora-adapters-directly-memory-efficient)
- [Deploying with Ollama](#deploying-with-ollama)
  - [Export GGUF first](#export-gguf-first-recommended--smaller-faster)
  - [Cleanup](#cleanup)
- [Troubleshooting](#troubleshooting)
- [Tuning Tips](#tuning-tips)
- [Resources](#resources)
- [Legacy](#legacy)

## Hardware Requirements

| Component | Minimum | This Setup |
|-----------|---------|------------|
| GPU VRAM  | 16 GB   | 16 GB      |
| RAM       | 32 GB   | 32 GB      |
| Disk      | 30 GB free | — |
| CUDA      | 12.1+   | —          |

Expected VRAM usage during training: ~13–15 GB (leaves comfortable headroom).

---

## Prerequisites

1. **NVIDIA drivers and CUDA toolkit** — verify with `nvidia-smi` and `nvcc --version`
2. **Python 3.11+** — `python3 --version`
3. **Hugging Face token** — Llama 3.1 is a gated model:
   - Go to https://huggingface.co/settings/tokens → New token → Role: Read
   - Accept the license at https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct
   - Copy the token (starts with `hf_...`)
   - Create your `.env` file:
     ```bash
     cp .env.example .env
     # Edit .env and replace hf_your_token_here with your actual token
     ```

---

## Setup

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install PyTorch with CUDA support
pip install torch --index-url https://download.pytorch.org/whl/cu126

# 3. Install remaining training dependencies
pip install -r requirements-training.txt

# Optional: Install Flash Attention 2 (requires system CUDA toolkit to match PyTorch's CUDA version)
# Check first: python -c "import torch; print(torch.version.cuda)" and nvcc --version
# If they match: pip install flash-attn --no-build-isolation
# If not, sdpa (the default) works well without it.
```

---

## Training

### Smoke test first (verifies setup, ~2 min)

```bash
python train.py --epochs 1 --max-steps 20
```

Expected output: loss around 1.0–2.0, no OOM errors.

### Full training run

```bash
python train.py --epochs 10 --batch-size 2 --grad-accum 4
```

| Setting | Value |
|---------|-------|
| Base model | Llama 3.1 8B Instruct |
| Quantization | 4-bit NF4 QLoRA |
| LoRA rank / alpha | 16 / 16 |
| Batch size | 2 (effective: 8 with grad accum 4) |
| Epochs | 10 |
| Learning rate | 2e-4 |
| Max sequence length | 2048 tokens |
| Attention | sdpa (PyTorch built-in) |
| Precision | bfloat16 |
| Peak RAM usage | ~9 GB |
| Expected time | ~8 minutes |
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

---

## Output Files

After training, the LoRA adapters are saved to `Model/oracle_cne_lora/`:

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
When loaded for inference on CUDA, bitsandbytes re-quantizes them to 4-bit in memory (~5 GB VRAM).
The 16-bit files are kept on disk so they can be used for GGUF export via llama.cpp.

---

## Monitoring Training

Training logs to stdout. Key lines to watch:

```
{'loss': 1.85, 'epoch': 0.1}   ← early loss (expected: 1.5–2.5)
{'loss': 0.85, 'epoch': 1.0}   ← after epoch 1 (expected: 0.7–1.2)
{'loss': 0.42, 'epoch': 3.0}   ← final (target: 0.3–0.5)
```

Eval loss is logged every 25 steps. If eval loss is significantly higher than train
loss (>0.3 gap), the model may be overfitting — reduce epochs or increase dropout.

To enable TensorBoard logging, install tensorboard and add `--report-to tensorboard`:
```bash
pip install tensorboard
# (re-run training with report_to="tensorboard" set in train.py)
tensorboard --logdir Model/checkpoints/runs
```

---

## Inference

### Using the merged 16-bit model

```bash
# Interactive mode
python inference.py

# Single question
python inference.py --question "How do I install OCNE on Oracle Linux?"
```

The script auto-detects CUDA → MPS → CPU in that order. On CUDA the model is loaded
in 4-bit quantization (~5 GB VRAM), which fits comfortably on a 16 GB GPU and produces
responses indistinguishable from 16-bit for Q&A tasks.

### Using LoRA adapters directly (memory-efficient)

Load adapters on top of the base model in your own script:

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B-Instruct")
model = PeftModel.from_pretrained(base, "Model/oracle_cne_lora")
tokenizer = AutoTokenizer.from_pretrained("Model/oracle_cne_lora")
```

---

## Deploying with Ollama

### Export GGUF first (recommended — smaller, faster)

Use a **separate venv** for llama.cpp — its dependencies (numpy, sentencepiece, gguf)
are unrelated to the training stack and should not be mixed with the project venv.

```bash
# Clone llama.cpp once alongside the project (i.e. ~/gitrepos/llama.cpp)
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Build llama-quantize (needed for the second step)
cmake -B build && cmake --build build --config Release -j$(nproc)

# Create and activate a dedicated venv for llama.cpp
python3 -m venv venv-llamacpp
source venv-llamacpp/bin/activate
pip install -r requirements.txt

# Step 1: Convert merged model to f16 GGUF
# (convert_hf_to_gguf.py no longer supports --outtype q4_k_m directly)
python3 convert_hf_to_gguf.py ../ocne-model-training/Model/oracle_cne_merged_16bit \
  --outfile ../ocne-model-training/Model/oracle_cne_f16.gguf \
  --outtype f16

# Step 2: Quantize to Q4_K_M
./build/bin/llama-quantize \
  ../ocne-model-training/Model/oracle_cne_f16.gguf \
  ../ocne-model-training/Model/oracle_cne_q4_k_m.gguf \
  Q4_K_M

# Clean up the intermediate f16 file (optional — it's ~15 GB)
rm ../ocne-model-training/Model/oracle_cne_f16.gguf

deactivate
```

Then import into Ollama (no Python needed — just ollama):

```bash
cd ..   # back to the project root
bash convert_to_ollama.sh
```

### Cleanup

After the model is imported into Ollama, free ~22 GB of intermediate files while keeping everything needed to retrain:

```bash
bash cleanup.sh
```

This removes the merged 16-bit model, the GGUF files, training checkpoints, and the llama.cpp build and venv. It keeps `venv/`, `Model/oracle_cne_lora/`, `Dataset/`, and `~/.cache/huggingface`.

---

## Troubleshooting

### Out of Memory (CUDA OOM) during training

The default settings (batch 2, grad accum 4) are tuned for 16 GB VRAM with ~9 GB peak
RAM. If you still hit OOM, reduce sequence length:
```bash
python train.py --max-seq-len 1024
```

### Flash Attention 2 compile error

Training defaults to `sdpa` (PyTorch built-in) which also uses Flash Attention kernels
automatically. Only use `--flash-attn` if you have the `flash-attn` package installed.

`flash-attn` requires the system CUDA toolkit version to match what PyTorch was built
against. Check with:
```bash
python -c "import torch; print(torch.version.cuda)"  # PyTorch CUDA version
nvcc --version                                         # system toolkit version
```
If they differ, `sdpa` is the correct default.

### `Error: Model not found` during training

The base model downloads automatically from Hugging Face on first run (~16 GB).
Make sure you have accepted the Llama 3.1 license and run `huggingface-cli login`.

### Training loss not decreasing

- Try increasing LoRA rank: `--lora-rank 32`
- Try more epochs: `--epochs 5`
- Check `Dataset/ocne_training_data.jsonl` for duplicate or malformed entries

### Slow training despite GPU

Confirm GPU is being used:
```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

---

## Tuning Tips

| Goal | Change |
|------|--------|
| Better quality | Increase `--lora-rank` to 32 or 64 |
| Faster training | Reduce `--max-seq-len` to 1024 |
| Prevent overfitting | Reduce `--epochs` to 2 |
| More stable training | Reduce `--lr` to 1e-4 |
| More creative responses | Increase temperature in `inference.py` |

---

## Resources

- [Llama 3.1 on Hugging Face](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)
- [PEFT documentation](https://huggingface.co/docs/peft)
- [TRL SFTTrainer documentation](https://huggingface.co/docs/trl/sft_trainer)
- [BitsAndBytes (QLoRA)](https://github.com/TimDettmers/bitsandbytes)
- [Flash Attention 2](https://github.com/Dao-AILab/flash-attention)
- [Oracle CNE documentation](https://docs.oracle.com/en/operating-systems/olcne/)

---

## Legacy

The original Google Colab notebook using Unsloth is kept for reference at
`Dataset/oracle_cne_unsloth_training.ipynb` but is no longer the recommended
training path.
