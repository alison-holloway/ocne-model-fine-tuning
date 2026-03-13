"""
generate_qa.py — Phase 2 of the dataset generation pipeline.

Reads content chunks produced by scrape_docs.py, calls a local Ollama model
to generate Q&A pairs per chunk, filters and deduplicates results, then writes
a timestamped JSONL file matching the format of ocne_training_data.jsonl.

Usage:
    python Dataset/generate_qa.py --dry-run
    python Dataset/generate_qa.py --pairs 3
    python Dataset/generate_qa.py --model llama32:latest --pairs 5
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

DEFAULT_MODEL = "llama32:latest"
DEFAULT_OLLAMA_URL = "http://localhost:11434"

PROMPT_TEMPLATE = """\
You are creating a training dataset for a model specializing in Oracle Cloud Native Environment (OCNE) documentation.

Given the following documentation excerpt, generate {n_pairs} question-and-answer pairs that a user might ask about this topic. Focus on practical, specific questions that have clear answers in the text.

Rules:
- Each question must be answerable from the provided text alone
- Answers must be specific and detailed, not vague
- Include relevant commands, YAML fields, or configuration values when present in the text
- Do not make up information not present in the text
- Format each pair exactly as shown below, with no extra text between pairs

Section: {section}
Heading: {heading}

Documentation text:
{text}

Generate {n_pairs} Q&A pairs in this exact format:
Q: <question here>
A: <answer here>
"""


def check_ollama(base_url, model):
    """
    Verify Ollama is running and the requested model is available.
    Exits with an error message if not.
    """
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=5)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Error: Cannot connect to Ollama at {base_url}", file=sys.stderr)
        print(f"  {e}", file=sys.stderr)
        print("Start Ollama with: ollama serve", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    available = [m["name"] for m in data.get("models", [])]

    if model not in available:
        print(f"Error: Model '{model}' not found in Ollama.", file=sys.stderr)
        print(f"Available models: {', '.join(available) or '(none)'}", file=sys.stderr)
        print(f"Pull it with: ollama pull {model}", file=sys.stderr)
        sys.exit(1)


def load_chunks(path, min_chunk=200):
    """Load chunks JSON, filter by minimum character count."""
    with open(path, encoding="utf-8") as f:
        chunks = json.load(f)

    before = len(chunks)
    chunks = [c for c in chunks if c.get("char_count", 0) >= min_chunk]
    print(f"Loaded {before} chunks, {len(chunks)} after filtering (min {min_chunk} chars)")
    return chunks


def build_prompt(chunk, n_pairs):
    """Build the Ollama prompt for a single chunk. Truncates text to 3000 chars."""
    text = chunk["text"][:3000]
    return PROMPT_TEMPLATE.format(
        n_pairs=n_pairs,
        section=chunk["section"],
        heading=chunk["heading"],
        text=text,
    )


def call_ollama(prompt, model, base_url):
    """
    POST to Ollama /api/generate. Returns the response text string or None on error.
    """
    try:
        resp = requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except requests.RequestException as e:
        print(f"  [ollama error] {e}", file=sys.stderr)
        return None


def parse_qa_pairs(raw_text):
    """
    Parse model output into list of {"instruction": ..., "response": ...} dicts.

    State machine handles:
      - Q: lines starting a new question
      - A: lines starting an answer
      - Multi-line answers (bullet points, code blocks, continued paragraphs)
    """
    pairs = []
    state = "SEEKING_Q"
    current_q = None
    current_a_lines = []

    for line in raw_text.splitlines():
        stripped = line.strip()

        if state == "SEEKING_Q":
            if stripped.lower().startswith("q:"):
                current_q = stripped[2:].strip()
                state = "SEEKING_A"

        elif state == "SEEKING_A":
            if stripped.lower().startswith("a:"):
                current_a_lines = [stripped[2:].strip()]
                state = "IN_ANSWER"
            elif stripped.lower().startswith("q:"):
                # Model skipped the answer — discard incomplete pair and start fresh
                current_q = stripped[2:].strip()

        elif state == "IN_ANSWER":
            if stripped.lower().startswith("q:"):
                # Save completed pair, start next question
                if current_q and current_a_lines:
                    pairs.append({
                        "instruction": current_q,
                        "response": "\n".join(current_a_lines).strip(),
                    })
                current_q = stripped[2:].strip()
                current_a_lines = []
                state = "SEEKING_A"
            else:
                # Continue collecting answer lines (including blank lines for formatting)
                current_a_lines.append(line.rstrip())

    # Save final pair
    if state == "IN_ANSWER" and current_q and current_a_lines:
        pairs.append({
            "instruction": current_q,
            "response": "\n".join(current_a_lines).strip(),
        })

    return pairs


def is_valid_pair(pair, min_answer):
    """Return True if the pair has a non-trivial question and a sufficiently long answer."""
    instruction = pair.get("instruction", "").strip()
    response = pair.get("response", "").strip()

    if not instruction or not response:
        return False
    if len(response) < min_answer:
        return False

    # Reject generic/placeholder answers
    generic = {"n/a", "not applicable", "not mentioned", "no information provided"}
    if response.lower() in generic:
        return False

    # Reject if the answer is just the heading text
    return True


def normalize(text):
    """Lowercase, collapse whitespace, strip punctuation for dedup comparison."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def dedup_pairs(pairs):
    """Remove pairs with duplicate questions (normalized). Keeps first occurrence."""
    seen = set()
    result = []
    for pair in pairs:
        key = normalize(pair["instruction"])
        if key not in seen:
            seen.add(key)
            result.append(pair)
    return result


def write_jsonl(pairs, path):
    """Write pairs to a JSONL file, one JSON object per line."""
    with open(path, "w", encoding="utf-8") as f:
        for pair in pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Q&A pairs from doc chunks using a local Ollama model.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--chunks",
        default="Dataset/ocne_chunks.json",
        help="Path to chunks JSON file (output of scrape_docs.py)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path for output JSONL (default: Dataset/ocne_generated_YYYYMMDD_HHMMSS.jsonl)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Ollama model name",
    )
    parser.add_argument(
        "--ollama-url",
        default=DEFAULT_OLLAMA_URL,
        help="Ollama API base URL",
    )
    parser.add_argument(
        "--pairs",
        type=int,
        default=3,
        help="Number of Q&A pairs to request per chunk",
    )
    parser.add_argument(
        "--min-answer",
        type=int,
        default=80,
        help="Minimum character count to keep a generated answer",
    )
    parser.add_argument(
        "--min-chunk",
        type=int,
        default=200,
        help="Minimum character count of input chunks to process",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds to sleep between Ollama API calls",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the prompt for the first chunk and exit",
    )
    args = parser.parse_args()

    # Resolve output path
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"Dataset/ocne_generated_{timestamp}.jsonl"

    # Load chunks
    if not Path(args.chunks).exists():
        print(f"Error: chunks file not found: {args.chunks}", file=sys.stderr)
        print("Run scrape_docs.py first.", file=sys.stderr)
        sys.exit(1)

    chunks = load_chunks(args.chunks, args.min_chunk)
    if not chunks:
        print("No chunks to process.", file=sys.stderr)
        sys.exit(1)

    # Dry run: show the first prompt and exit
    if args.dry_run:
        print("=== DRY RUN — first chunk prompt ===\n")
        print(build_prompt(chunks[0], args.pairs))
        return

    # Preflight: verify Ollama is up and model exists
    check_ollama(args.ollama_url, args.model)
    print(f"Model: {args.model}  |  Ollama: {args.ollama_url}")
    print(f"Processing {len(chunks)} chunks, requesting {args.pairs} pairs each")
    print(f"Output: {args.output}\n")

    all_pairs = []
    raw_count = 0

    for i, chunk in enumerate(chunks, 1):
        print(f"\r[{i}/{len(chunks)}] {chunk['section']}: {chunk['heading'][:60]}", end="", flush=True)

        prompt = build_prompt(chunk, args.pairs)
        raw = call_ollama(prompt, args.model, args.ollama_url)

        if raw:
            pairs = parse_qa_pairs(raw)
            valid = [p for p in pairs if is_valid_pair(p, args.min_answer)]
            raw_count += len(pairs)
            all_pairs.extend(valid)

        time.sleep(args.delay)

    print()  # newline after progress line

    # Deduplicate across all chunks
    before_dedup = len(all_pairs)
    all_pairs = dedup_pairs(all_pairs)

    # Write output
    write_jsonl(all_pairs, args.output)

    print(f"\nDone.")
    print(f"  Chunks processed : {len(chunks)}")
    print(f"  Raw pairs        : {raw_count}")
    print(f"  After filtering  : {before_dedup}")
    print(f"  After dedup      : {len(all_pairs)}")
    print(f"  Written to       : {args.output}")
    print()
    print("Review the output, then merge with:")
    print(f"  cat {args.output} >> Dataset/ocne_training_data.jsonl")


if __name__ == "__main__":
    main()
