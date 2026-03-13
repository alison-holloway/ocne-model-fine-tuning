"""
Oracle CNE Fine-tuned Model - Local Inference Script
Loads the merged 16-bit model on NVIDIA GPU (CUDA), Apple Silicon (MPS), or CPU.

Usage:
    python inference.py
    python inference.py --question "How do I create a cluster with ocne?"
    python inference.py --cpu  # Force CPU if GPU runs out of memory
"""

import argparse
import os
import sys
from pathlib import Path

import torch
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

MODEL_PATH = Path(__file__).parent / "Model" / "oracle_cne_merged_16bit"

SYSTEM_PROMPT = (
    "You are an expert on Oracle Cloud Native Environment (CNE). "
    "Provide accurate, detailed, and helpful answers based on the official "
    "Oracle CNE documentation. Include specific commands, configuration "
    "details, and best practices when relevant."
)


def get_device(force_cpu: bool = False) -> str:
    if force_cpu:
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_model(device: str):
    print(f"Loading model from {MODEL_PATH}")
    print(f"Device: {device}")
    print("Loading 16-bit weights from disk, quantizing to 4-bit in VRAM (~5 GB)..." if device == "cuda" else "This may take a minute and use significant memory (~15 GB)...")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

    if device == "cuda":
        # 4-bit quantization keeps VRAM under 6GB, leaving room for generation
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            quantization_config=bnb_config,
            device_map="auto",
        )
    else:
        dtype = torch.float16
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            dtype=dtype,
            low_cpu_mem_usage=True,
        )
        model.to(device)
    model.eval()

    print("Model loaded successfully.\n")
    return model, tokenizer


def ask(model, tokenizer, question: str, device: str, max_new_tokens: int = 512):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    tokenized = tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, return_tensors="pt"
    )
    # transformers 4.47+ returns a BatchEncoding; older versions return a plain tensor
    if hasattr(tokenized, "input_ids"):
        input_ids = tokenized.input_ids.to(device)
    else:
        input_ids = tokenized.to(device)

    with torch.no_grad():
        output_ids = model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
        )

    # Decode only the generated tokens (skip the prompt)
    response = tokenizer.decode(
        output_ids[0][input_ids.shape[1]:], skip_special_tokens=True
    )
    return response.strip()


def interactive_mode(model, tokenizer, device: str):
    print("Oracle CNE Assistant - Interactive Mode")
    print("Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            question = input("Question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        print("\nGenerating response...\n")
        response = ask(model, tokenizer, question, device)
        print(f"Answer: {response}\n")


def main():
    parser = argparse.ArgumentParser(description="Oracle CNE model inference")
    parser.add_argument("--question", "-q", type=str, help="Single question to ask")
    parser.add_argument(
        "--cpu", action="store_true", help="Force CPU instead of GPU"
    )
    parser.add_argument(
        "--max-tokens", type=int, default=512, help="Max tokens to generate"
    )
    args = parser.parse_args()

    load_dotenv()
    token = os.environ.get("HUGGING_FACE_TOKEN")
    if token:
        os.environ["HF_TOKEN"] = token

    if not MODEL_PATH.exists():
        print(f"Error: Model not found at {MODEL_PATH}")
        print("Make sure the merged 16-bit model is in the Model/ directory.")
        sys.exit(1)

    device = get_device(force_cpu=args.cpu)
    model, tokenizer = load_model(device)

    if args.question:
        response = ask(model, tokenizer, args.question, device, args.max_tokens)
        print(f"Answer: {response}")
    else:
        interactive_mode(model, tokenizer, device)


if __name__ == "__main__":
    main()
