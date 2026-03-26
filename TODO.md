# TODO

## Evaluate model before and after training

Establish a baseline with the unmodified Llama 3.1 8B Instruct model, then compare against the fine-tuned model to measure the benefit of fine-tuning on OCNE-specific content.

### Steps

1. Select a set of representative OCNE questions to use as an eval set — ideally questions not present in `Dataset/ocne_training_data.jsonl`.

2. Run the base model (`meta-llama/Llama-3.1-8B-Instruct`) against the eval questions before training and record the responses.

3. Train the model:
   ```bash
   python train.py --merge
   ```

4. Run `inference.py` against the same eval questions and record the responses.

5. Compare responses qualitatively: accuracy, specificity, correct command syntax, hallucinations.

6. Optionally compute a quantitative metric (e.g. ROUGE or BERTScore) against reference answers.

---

## Test dataset generation with llama3.1:8b

The dataset generation pipeline has only been tested with `llama3.2` (3B). Test with a larger model to evaluate Q&A pair quality.

### Steps

1. Pull the model:
   ```bash
   ollama pull llama3.1:8b
   ```

2. Scrape the docs (or reuse an existing `Dataset/ocne_chunks.json`):
   ```bash
   python Dataset/scrape_docs.py --verbose
   ```

3. Dry-run to verify the prompt looks correct:
   ```bash
   python Dataset/generate_qa.py --model llama3.1:8b --dry-run
   ```

4. Generate a small sample to compare quality (scrape one section first, then generate from it):
   ```bash
   python Dataset/scrape_docs.py --sections concepts --output Dataset/ocne_chunks_test.json --verbose
   python Dataset/generate_qa.py --model llama3.1:8b --pairs 3 --chunks Dataset/ocne_chunks_test.json
   ```

5. Compare output quality against the existing `llama3.2`-generated pairs in `Dataset/ocne_training_data.jsonl`.

6. If quality is better, update the README to recommend `llama3.1:8b` as the default and update `DEFAULT_MODEL` in `Dataset/generate_qa.py`.
