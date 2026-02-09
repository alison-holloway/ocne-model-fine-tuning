# Oracle CNE Model Training

Fine-tune Llama 3.1 8B on Oracle Cloud Native Environment (CNE) documentation using [Unsloth](https://github.com/unslothai/unsloth) for efficient QLoRA training on Google Colab's free tier (T4 GPU).

## Overview

This project provides everything needed to create a specialized AI assistant for Oracle Cloud Native Environment:

- **Training notebook** optimized for Google Colab free tier (T4 GPU, 16GB VRAM)
- **285 curated Q&A pairs** covering CLI usage, cluster management, concepts, and quick start guides
- **4-bit quantization** with QLoRA for memory-efficient training
- **Multiple deployment options**: Python inference, Ollama, vLLM

## Repository Structure

```
Dataset/
  ocne_training_data.jsonl           # 285 Q&A pairs in JSONL format
  oracle_cne_unsloth_training.ipynb  # Training notebook for Google Colab
  ocne_cli_training_qa.md            # Source Q&A: CLI reference
  ocne_clusters_training_qa.md       # Source Q&A: cluster management
  ocne_concepts_training_qa.md       # Source Q&A: concepts guide
  ocne_quick_start_training_qa.md    # Source Q&A: quick start guide
inference.py                         # Local inference script (MPS/CPU)
convert_to_ollama.sh                 # Convert model to Ollama format
Modelfile                            # Ollama model configuration
plan.md                              # Detailed training guide and troubleshooting
```

## Quick Start

1. Open `Dataset/oracle_cne_unsloth_training.ipynb` in [Google Colab](https://colab.research.google.com/)
2. Set runtime to **T4 GPU** (`Runtime > Change runtime type`)
3. Upload `Dataset/ocne_training_data.jsonl` when prompted
4. Run all cells -- training takes approximately 15-30 minutes

## Training Details

| Parameter | Value |
|-----------|-------|
| Base model | Llama 3.1 8B Instruct |
| Method | QLoRA (4-bit quantization) |
| LoRA rank | 16 |
| Training samples | 285 (256 train / 29 validation) |
| Epochs | 3 |
| Effective batch size | 8 |
| Training time | ~15-30 min on T4 GPU |
| Expected final loss | 0.3-0.5 |

## Dataset

The training data covers four areas of Oracle CNE documentation:

- **CLI Reference** - Command syntax, completion, environment variables, configuration
- **Cluster Management** - Provider types (libvirt, OCI, OLVM, BYO), scaling, updates
- **Concepts** - Architecture, components, OCK images, networking
- **Quick Start** - Installation, first cluster creation, application deployment

## Model Outputs

After training, the notebook produces:
- **LoRA adapters** (~100-200MB) - lightweight, requires base Llama 3.1 8B
- **Merged 16-bit model** (~16GB, optional) - standalone, no base model needed
- **Merged 4-bit model** (~4-5GB, optional) - smallest standalone option
- **GGUF for Ollama** (~4.5GB, optional) - pre-quantized, recommended for Ollama deployment

Model files are not included in this repository due to size. See [plan.md](plan.md) for deployment instructions including Ollama and vLLM.

## Deployment

### Local Inference (Python)

Run the model locally on Apple Silicon (MPS) or CPU:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Interactive mode
python inference.py

# Single question
python inference.py --question "How do I create a cluster with ocne?"

# Force CPU if MPS runs out of memory
python inference.py --cpu
```

### Ollama

Import the model into Ollama for easy local serving:

```bash
brew install ollama
ollama serve  # in another terminal, or use the Ollama app

./convert_to_ollama.sh
ollama run oracle-cne
```

The script auto-detects the model format in `Model/`:
- **GGUF file** (recommended) - lightweight import, works on Macs with 16GB RAM. Export from the Colab notebook by setting `save_gguf=True`, then place the `.gguf` file in `Model/`.
- **Safetensors fallback** - converts on-device, requires 32GB+ RAM. The script will warn before proceeding.

## Documentation

See [plan.md](plan.md) for the complete training guide, including:
- Detailed step-by-step instructions
- Troubleshooting (OOM errors, slow training, disconnections)
- Hyperparameter tuning advice
- Deployment with Ollama, vLLM, or Python
- Tips for improving model quality

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

Note: Usage of the fine-tuned model is subject to the [Llama 3.1 license](https://llama.meta.com/llama3_1/license/) and Oracle documentation usage policies.
