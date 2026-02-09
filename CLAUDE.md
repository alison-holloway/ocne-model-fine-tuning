# CLAUDE.md

## Project Overview

This project fine-tunes Llama 3.1 8B on Oracle Cloud Native Environment (CNE) documentation using Unsloth with QLoRA. Training runs on Google Colab's free tier (T4 GPU).

## Repository Structure

- `Dataset/` - Training data (285 Q&A pairs in JSONL) and the Colab training notebook
- `Model/` - Local-only trained model outputs (gitignored, 27GB+)
- `venv/` - Python 3.14 virtual environment (gitignored)
- `plan.md` - Detailed training guide, troubleshooting, and deployment instructions

## Key Files

- `Dataset/oracle_cne_unsloth_training.ipynb` - Main training notebook (designed for Google Colab)
- `Dataset/ocne_training_data.jsonl` - Training dataset (285 instruction/response pairs)
- `Dataset/ocne_*_training_qa.md` - Source Q&A markdown files used to generate the JSONL

## Important Notes

- Never commit files in `Model/` - they are 27GB+ of trained model weights
- The notebook is designed for Colab, not local execution
- Training dependencies (unsloth, trl, peft, bitsandbytes) are installed by the notebook at runtime
- `requirements.txt` covers local inference dependencies only
