# Oracle CNE Fine-tuning Guide with Unsloth

Complete guide for fine-tuning Llama 3.1 8B on Oracle Cloud Native Environment documentation using Unsloth on Google Colab free tier.

## 📋 Prerequisites

- Google account (for Colab)
- `ocne_training_data.jsonl` file (285 Q&A pairs)
- Basic understanding of machine learning concepts

## 🚀 Quick Start

### 1. Open Google Colab
1. Go to [Google Colab](https://colab.research.google.com/)
2. Upload the `oracle_cne_unsloth_training.ipynb` notebook
3. Or use: `File → Upload notebook`

### 2. Enable GPU
1. Go to `Runtime → Change runtime type`
2. Select `T4 GPU` under Hardware accelerator
3. Click Save

### 3. Upload Training Data
When prompted in the notebook (Step 4), upload your `ocne_training_data.jsonl` file.

### 4. Run All Cells
- Use `Runtime → Run all` or run cells sequentially
- Training takes approximately 15-30 minutes on T4 GPU

## 📊 What to Expect

### Training Configuration
- **Model**: Llama 3.1 8B Instruct
- **Training samples**: 285 (256 train, 29 validation)
- **Epochs**: 3
- **Effective batch size**: 8
- **Memory usage**: ~14-15GB VRAM (fits T4)
- **Training time**: 15-30 minutes

### Expected Results
- Final training loss: ~0.3-0.5 (lower is better)
- The model should accurately answer Oracle CNE technical questions
- Responses should be detailed and match documentation style

## 🔧 Troubleshooting

### Out of Memory Error
**Symptoms**: CUDA out of memory error during training

**Solutions**:
1. Reduce batch size in Step 7:
   ```python
   per_device_train_batch_size=1,
   gradient_accumulation_steps=8,
   ```
2. Reduce max sequence length:
   ```python
   max_seq_length=1024
   ```

### Slow Training
**Symptoms**: Training is very slow or stuck

**Solutions**:
1. Ensure GPU is enabled (should say T4 in Colab)
2. Restart runtime: `Runtime → Restart runtime`
3. Check GPU usage: `!nvidia-smi`

### Poor Model Performance
**Symptoms**: Model gives generic or incorrect answers

**Solutions**:
1. Increase epochs to 5-7:
   ```python
   num_train_epochs=5
   ```
2. Lower learning rate:
   ```python
   learning_rate=1e-4
   ```
3. Add more training data if available

### Disconnection Issues
**Symptom**: Colab disconnects during training

**Solutions**:
1. Keep the Colab tab active
2. Use Colab Pro for longer runtimes
3. Save checkpoints (already configured every 50 steps)

## 📁 Output Files

After training, you'll have:

### LoRA Adapters (Recommended)
- **Location**: `oracle_cne_lora_model/`
- **Size**: ~100-200MB
- **Contains**: 
  - `adapter_config.json`
  - `adapter_model.safetensors`
  - `tokenizer_config.json`
  - Other tokenizer files

**Usage**: Load with base Llama 3.1 8B + these adapters

### Merged Models (Optional)
If you chose to save merged models:
- **16-bit merged**: `oracle_cne_merged_16bit/` (~16GB)
- **4-bit merged**: `oracle_cne_merged_4bit/` (~4-5GB)

**Usage**: Standalone models, no base model needed

## 🎯 Using Your Fine-tuned Model

### Option 1: In Colab (Immediate Testing)
Use the interactive testing cells (Steps 11-12) in the notebook.

### Option 2: Load in Python
```python
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="oracle_cne_lora_model",
    max_seq_length=2048,
    load_in_4bit=True,
)

FastLanguageModel.for_inference(model)

# Use the model
inputs = tokenizer(["Your question here"], return_tensors="pt").to("cuda")
outputs = model.generate(**inputs, max_new_tokens=512)
print(tokenizer.decode(outputs[0]))
```

### Option 3: Deploy with Ollama
1. Convert to GGUF format:
   ```bash
   python convert_hf_to_gguf.py oracle_cne_merged_16bit \
     --outtype q4_k_m \
     --outfile oracle-cne-q4.gguf
   ```
2. Create Modelfile:
   ```
   FROM ./oracle-cne-q4.gguf
   TEMPLATE """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
   You are an Oracle CNE expert...<|eot_id|>..."""
   ```
3. Import: `ollama create oracle-cne -f Modelfile`
4. Run: `ollama run oracle-cne`

### Option 4: Deploy with vLLM
```python
from vllm import LLM, SamplingParams

llm = LLM(model="oracle_cne_merged_16bit")
sampling_params = SamplingParams(temperature=0.7, max_tokens=512)

outputs = llm.generate(["Your question"], sampling_params)
print(outputs[0].outputs[0].text)
```

## 🎛️ Advanced Customization

### Adjust Training Duration
In Step 7, modify:
```python
num_train_epochs=5,  # More epochs for better learning
```

### Change Learning Rate
```python
learning_rate=1e-4,  # Lower = more stable, higher = faster
```

### Modify LoRA Rank
In Step 3, change `r` value:
```python
r=32,  # Higher = more parameters, better quality, slower
```

### Adjust Temperature (Inference)
In Step 11:
```python
temperature=0.7,  # Lower = more focused, higher = more creative
```

## 📈 Monitoring Training

### Key Metrics to Watch

1. **Training Loss**: Should decrease over time
   - Good: 0.3-0.5
   - Concerning: Not decreasing or increasing

2. **Validation Loss**: Should follow training loss
   - If much higher than training loss = overfitting

3. **GPU Memory**: Should stay under 16GB
   - Check with: `!nvidia-smi`

### Training Logs
Look for patterns like:
```
{'loss': 0.8123, 'learning_rate': 0.0002, 'epoch': 0.5}
{'loss': 0.5234, 'learning_rate': 0.00015, 'epoch': 1.0}
{'loss': 0.3456, 'learning_rate': 0.0001, 'epoch': 1.5}
```

## 💡 Tips for Best Results

### 1. Data Quality
- Ensure Q&A pairs are accurate and well-formatted
- Remove duplicates or very similar questions
- Balance question types (conceptual, procedural, troubleshooting)

### 2. Training Settings
- Start with default settings
- If loss plateaus, try:
  - Lower learning rate
  - More epochs
  - Higher LoRA rank

### 3. Evaluation
- Test on diverse questions not in training data
- Compare answers to official documentation
- Check for hallucinations or incorrect information

### 4. Iteration
- Fine-tuning is iterative
- Save different versions with different hyperparameters
- Keep notes on what works

## 🔒 Best Practices

### Security
- Don't include sensitive information in training data
- Be cautious when uploading to public repositories
- Use private HuggingFace repos if sharing

### Resource Management
- Close Colab sessions when done to free resources
- Download models before session ends (12 hours on free tier)
- Use Google Drive for persistent storage

### Version Control
- Keep track of training data versions
- Note hyperparameters for each training run
- Save training logs and metrics

## 📚 Additional Resources

### Unsloth Documentation
- [GitHub](https://github.com/unslothai/unsloth)
- [Documentation](https://docs.unsloth.ai/)

### Llama 3.1 Resources
- [Model Card](https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct)
- [Prompt Format](https://llama.meta.com/docs/model-cards-and-prompt-formats/meta-llama-3/)

### Oracle CNE Documentation
- [Official Docs](https://docs.oracle.com/en/operating-systems/olcne/)
- [CLI Reference](https://docs.oracle.com/en/operating-systems/olcne/cli/)

## ❓ FAQ

**Q: Can I use a different model?**  
A: Yes! Change the model name in Step 2:
```python
model_name="unsloth/Meta-Llama-3.1-70B-Instruct"  # Needs more GPU
model_name="unsloth/mistral-7b-v0.3"  # Alternative
```

**Q: How do I add more training data?**  
A: Simply append new Q&A pairs to your JSONL file in the same format.

**Q: Can I continue training from a checkpoint?**  
A: Yes! Load the saved model and run training again with more epochs.

**Q: Why use LoRA instead of full fine-tuning?**  
A: LoRA is much more memory-efficient, allowing training on free GPUs while maintaining quality.

**Q: How do I evaluate model quality?**  
A: Test on held-out questions, compare to documentation, and check for factual accuracy.

## 🤝 Contributing

Have improvements or found issues?
- Share your training configurations
- Report bugs or inconsistencies
- Suggest additional features

## 📄 License

This training notebook is provided as-is for educational purposes. Ensure compliance with:
- Llama 3.1 license for model usage
- Oracle documentation usage policies
- Your organization's data policies

---

**Happy Training! 🚀**

For questions or issues, refer to the Unsloth documentation or Oracle CNE community forums.
