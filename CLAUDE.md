# CLAUDE.md

## Project Overview

This project fine-tunes Llama 3.1 8B on Oracle Cloud Native Environment (CNE) documentation using QLoRA on a local NVIDIA GPU (16 GB VRAM, 32 GB RAM). Training uses the standard HuggingFace stack (transformers + peft + trl + bitsandbytes) — no Unsloth or cloud services required.

## Repository Structure

- `Dataset/` - Training data (285 Q&A pairs in JSONL) and a legacy Colab notebook
- `Model/` - Local-only trained model outputs (gitignored)
- `venv/` - Python 3.11 virtual environment (gitignored)
- `README.md` - Full guide covering setup, dataset generation, training, inference, deployment, and troubleshooting

## Key Files

- `train.py` - Main training script (local GPU, QLoRA)
- `inference.py` - Local inference script (CUDA / MPS / CPU)
- `Dataset/ocne_training_data.jsonl` - Training dataset (285 instruction/response pairs)
- `Dataset/ocne_*_training_qa.md` - Source Q&A markdown files used to generate the JSONL
- `.env.example` - Template for Hugging Face token config (copy to `.env`)
- `requirements.txt` - All dependencies (training, inference, dataset generation)

## Important Notes

- Never commit files in `Model/` - they are large trained model weights
- Never commit `.env` - it contains the Hugging Face token (already in .gitignore)
- `requirements.txt` covers training, inference, and dataset generation
- The legacy Colab notebook (`Dataset/oracle_cne_unsloth_training.ipynb`) is kept for reference only
- Inference loads the merged model in 4-bit quantization on CUDA (~5 GB VRAM)
