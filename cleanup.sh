#!/bin/bash
#
# Clean up large intermediate files that are no longer needed after Ollama import.
#
# Keeps everything needed to retrain:
#   - venv/                          training dependencies
#   - Model/oracle_cne_lora/         LoRA adapters
#   - ~/.cache/huggingface           base Llama 3.1 8B weights
#   - Dataset/                       training data
#
# Removes files that are safe to delete after the model is in Ollama:
#   - Model/oracle_cne_merged_16bit/ 16-bit merged model (~15 GB, only needed for GGUF export)
#   - Model/oracle_cne_q4_k_m.gguf  quantized GGUF (~4.6 GB, Ollama has its own copy)
#   - Model/oracle_cne_f16.gguf      intermediate f16 GGUF if not already removed (~15 GB)
#   - Model/checkpoints/             training checkpoints (~357 MB)
#   - ../llama.cpp/build             cmake build artifacts (~270 MB)
#   - ../llama.cpp/venv-llamacpp     llama.cpp Python venv (~1.3 GB)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LLAMACPP_DIR="$(dirname "$SCRIPT_DIR")/llama.cpp"

echo "=== OCNE Model Cleanup ==="
echo "Keeping: venv/, Model/oracle_cne_lora/, Dataset/, ~/.cache/huggingface"
echo ""

# Compute total to be freed
total=0
declare -a targets=(
    "$SCRIPT_DIR/Model/oracle_cne_merged_16bit"
    "$SCRIPT_DIR/Model/oracle_cne_q4_k_m.gguf"
    "$SCRIPT_DIR/Model/oracle_cne_f16.gguf"
    "$SCRIPT_DIR/Model/checkpoints"
    "$LLAMACPP_DIR/build"
    "$LLAMACPP_DIR/venv-llamacpp"
)

for path in "${targets[@]}"; do
    if [[ -e "$path" ]]; then
        size=$(du -sh "$path" 2>/dev/null | cut -f1)
        echo "  Will remove: $path  ($size)"
        total=1
    fi
done

if [[ $total -eq 0 ]]; then
    echo "Nothing to clean up — all targets already removed."
    exit 0
fi

echo ""
read -r -p "Proceed? [y/N] " response
if [[ ! "${response}" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
for path in "${targets[@]}"; do
    if [[ -e "$path" ]]; then
        echo "Removing $path..."
        rm -rf "$path"
    fi
done

echo ""
echo "Done. Disk usage of remaining model files:"
du -sh "$SCRIPT_DIR/Model/"* 2>/dev/null || echo "  (Model/ is empty)"
