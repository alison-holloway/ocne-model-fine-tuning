#!/usr/bin/env python3
"""
Fine-tune Llama 3.1 8B on OCNE documentation using QLoRA.

Requires a CUDA-enabled GPU with 16GB+ VRAM.

Setup:
    pip install torch --index-url https://download.pytorch.org/whl/cu126
    pip install flash-attn --no-build-isolation
    pip install -r requirements-training.txt

Usage:
    python train.py                          # full training run
    python train.py --epochs 1 --max-steps 20  # smoke test
    python train.py --merge                  # train + merge to 16-bit
    python train.py --help
"""

import argparse
import os
import sys

import torch
from dotenv import load_dotenv
from datasets import load_dataset
from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
DATASET_PATH = "Dataset/ocne_training_data.jsonl"
LORA_OUTPUT_DIR = "Model/oracle_cne_lora"
MERGED_OUTPUT_DIR = "Model/oracle_cne_merged_16bit"
CHECKPOINT_DIR = "Model/checkpoints"

SYSTEM_PROMPT = (
    "You are an expert on Oracle Cloud Native Environment (CNE). "
    "Provide accurate, detailed technical answers based on official documentation."
)

# LoRA target modules — all linear projection layers in Llama 3.1
LORA_TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tune Llama 3.1 8B on OCNE documentation (QLoRA, local GPU)"
    )
    parser.add_argument("--base-model", default=BASE_MODEL,
                        help="HuggingFace model ID or local path")
    parser.add_argument("--dataset", default=DATASET_PATH,
                        help="Path to JSONL training data")
    parser.add_argument("--output-dir", default=LORA_OUTPUT_DIR,
                        help="Where to save LoRA adapters")
    parser.add_argument("--epochs", type=int, default=10,
                        help="Number of training epochs (default: 10)")
    parser.add_argument("--batch-size", type=int, default=2,
                        help="Per-device train batch size (default: 2)")
    parser.add_argument("--grad-accum", type=int, default=4,
                        help="Gradient accumulation steps (default: 4, effective batch=8)")
    parser.add_argument("--lr", type=float, default=2e-4,
                        help="Learning rate (default: 2e-4)")
    parser.add_argument("--lora-rank", type=int, default=16,
                        help="LoRA rank r (default: 16)")
    parser.add_argument("--lora-alpha", type=int, default=16,
                        help="LoRA alpha (default: 16)")
    parser.add_argument("--max-seq-len", type=int, default=2048,
                        help="Maximum token sequence length (default: 2048)")
    parser.add_argument("--max-steps", type=int, default=-1,
                        help="Override epochs with a fixed step count (useful for smoke tests)")
    parser.add_argument("--merge", action="store_true",
                        help="After training, merge LoRA weights into base model and save 16-bit")
    parser.add_argument("--flash-attn", action="store_true",
                        help="Use flash_attention_2 (requires flash-attn package). Default: sdpa (built into PyTorch)")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def format_prompt(example: dict, tokenizer: AutoTokenizer) -> dict:
    """Apply Llama 3.1 chat template to a single instruction/response example."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": example["instruction"]},
        {"role": "assistant", "content": example["response"]},
    ]
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=False
    )
    return {"text": text}


def load_and_prepare_dataset(dataset_path: str, tokenizer: AutoTokenizer):
    """Load JSONL, apply chat template, split 90/10 train/val."""
    if not os.path.exists(dataset_path):
        print(f"ERROR: Dataset not found at {dataset_path}", file=sys.stderr)
        sys.exit(1)

    raw = load_dataset("json", data_files=dataset_path, split="train")
    formatted = raw.map(lambda ex: format_prompt(ex, tokenizer))

    split = formatted.train_test_split(test_size=0.1, seed=42)
    train_ds = split["train"]
    val_ds = split["test"]

    print(f"Dataset: {len(train_ds)} train / {len(val_ds)} validation samples")
    return train_ds, val_ds


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

def load_model_and_tokenizer(
    model_id: str,
    use_flash_attn: bool = True,
) -> tuple[AutoModelForCausalLM, AutoTokenizer]:
    """Load base model in 4-bit QLoRA configuration."""
    print(f"Loading base model: {model_id}")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    attn_impl = "flash_attention_2" if use_flash_attn else "sdpa"
    print(f"Attention implementation: {attn_impl}")

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto",
        attn_implementation=attn_impl,
    )
    model = prepare_model_for_kbit_training(model)

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id

    return model, tokenizer


def apply_lora(
    model: AutoModelForCausalLM,
    rank: int,
    alpha: int,
) -> AutoModelForCausalLM:
    """Wrap model with LoRA adapters."""
    lora_config = LoraConfig(
        r=rank,
        lora_alpha=alpha,
        target_modules=LORA_TARGET_MODULES,
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    return model


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train(args: argparse.Namespace) -> None:
    load_dotenv()
    token = os.environ.get("HUGGING_FACE_TOKEN")
    if not token:
        print("ERROR: HUGGING_FACE_TOKEN not set. Copy .env.example to .env and add your token.", file=sys.stderr)
        sys.exit(1)
    os.environ["HF_TOKEN"] = token  # used by transformers / huggingface_hub

    if not torch.cuda.is_available():
        print("WARNING: No CUDA GPU detected. Training on CPU will be extremely slow.")

    model, tokenizer = load_model_and_tokenizer(args.base_model, use_flash_attn=args.flash_attn)
    model = apply_lora(model, rank=args.lora_rank, alpha=args.lora_alpha)

    train_ds, val_ds = load_and_prepare_dataset(args.dataset, tokenizer)

    training_args = SFTConfig(
        output_dir=CHECKPOINT_DIR,
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,          # -1 means use num_train_epochs
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        warmup_steps=5,
        optim="adamw_bnb_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        bf16=True,
        gradient_checkpointing=True,
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=25,
        save_steps=50,
        save_total_limit=2,
        load_best_model_at_end=True,
        max_length=args.max_seq_len,
        dataset_text_field="text",
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        processing_class=tokenizer,
    )

    print("Starting training...")
    trainer.train()

    print(f"Saving LoRA adapters to {args.output_dir} ...")
    os.makedirs(args.output_dir, exist_ok=True)
    trainer.model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print("LoRA adapters saved.")

    if args.merge:
        merge_and_save(trainer.model, tokenizer, args.base_model)


# ---------------------------------------------------------------------------
# Optional: merge adapters into base model
# ---------------------------------------------------------------------------

def merge_and_save(
    peft_model,
    tokenizer: AutoTokenizer,
    base_model_id: str,
) -> None:
    """Merge LoRA weights into the base model and save as 16-bit safetensors."""
    print(f"Merging LoRA into base model and saving to {MERGED_OUTPUT_DIR} ...")
    print("This requires ~16GB of free RAM in addition to VRAM.")

    merged = peft_model.merge_and_unload()
    os.makedirs(MERGED_OUTPUT_DIR, exist_ok=True)
    merged.save_pretrained(MERGED_OUTPUT_DIR, safe_serialization=True)
    tokenizer.save_pretrained(MERGED_OUTPUT_DIR)
    print(f"Merged model saved to {MERGED_OUTPUT_DIR}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = parse_args()
    train(args)
