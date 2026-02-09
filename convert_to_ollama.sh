#!/bin/bash
#
# Import the fine-tuned Oracle CNE model into Ollama.
#
# By default, uses a pre-quantized GGUF file (exported from Colab).
# This is the recommended approach — it avoids the ~16GB+ memory spike
# that occurs when Ollama converts safetensors locally, which can crash
# Macs with 16GB RAM.
#
# If no GGUF file is found, falls back to the merged 16-bit safetensors
# model (requires 32GB+ RAM for conversion).
#
# Prerequisites:
#   brew install ollama
#   ollama serve  (in another terminal, or use the Ollama app)
#
# Usage:
#   ./convert_to_ollama.sh              # auto-detect GGUF or safetensors
#   ./convert_to_ollama.sh --16bit      # force safetensors (needs 32GB+ RAM)
#   ollama run oracle-cne

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODEL_DIR="${SCRIPT_DIR}/Model"
MODEL_NAME="oracle-cne"
MODELFILE="${SCRIPT_DIR}/Modelfile"

FORCE_16BIT=false
if [[ "${1:-}" == "--16bit" ]]; then
    FORCE_16BIT=true
fi

# --- Preflight checks ---

if ! command -v ollama &> /dev/null; then
    echo "Error: ollama is not installed."
    echo "Install with: brew install ollama"
    exit 1
fi

if ! ollama list &> /dev/null 2>&1; then
    echo "Error: ollama is not running."
    echo "Start it with: ollama serve (or open the Ollama app)"
    exit 1
fi

# --- Detect model format ---

GGUF_FILE=""
if [[ "${FORCE_16BIT}" == false ]]; then
    # Look for a GGUF file in Model/
    for f in "${MODEL_DIR}"/*.gguf; do
        if [[ -f "$f" ]]; then
            GGUF_FILE="$f"
            break
        fi
    done
fi

if [[ -n "${GGUF_FILE}" ]]; then
    # --- GGUF path (recommended, low memory) ---
    GGUF_BASENAME=$(basename "${GGUF_FILE}")
    echo "Found GGUF file: ${GGUF_BASENAME}"
    echo "Using pre-quantized GGUF (lightweight import, no heavy conversion needed)."

    cat > "${MODELFILE}" << TEMPLATE_END
# Oracle CNE Fine-tuned Model
# Based on Llama 3.1 8B Instruct, fine-tuned on Oracle CNE documentation

FROM ./Model/${GGUF_BASENAME}

SYSTEM """You are an expert on Oracle Cloud Native Environment (CNE). Provide accurate, detailed, and helpful answers based on the official Oracle CNE documentation. Include specific commands, configuration details, and best practices when relevant."""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER stop <|eot_id|>
PARAMETER stop <|end_of_text|>
TEMPLATE_END

else
    # --- Safetensors fallback (high memory) ---
    SAFETENSORS_DIR="${MODEL_DIR}/oracle_cne_merged_16bit"

    if [[ ! -d "${SAFETENSORS_DIR}" ]]; then
        echo "Error: No model found in ${MODEL_DIR}/"
        echo ""
        echo "Expected one of:"
        echo "  - Model/*.gguf          (recommended, export from Colab with save_gguf=True)"
        echo "  - Model/oracle_cne_merged_16bit/  (safetensors, needs 32GB+ RAM to convert)"
        exit 1
    fi

    echo "WARNING: No GGUF file found in Model/. Falling back to safetensors conversion."
    echo "This requires ~32GB RAM. On Macs with 16GB RAM, this will likely crash."
    echo ""
    echo "Recommended: Re-run the Colab notebook with save_gguf=True to export a"
    echo "pre-quantized GGUF file, then place it in the Model/ directory."
    echo ""
    read -r -p "Continue anyway? [y/N] " response
    if [[ ! "${response}" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi

    cat > "${MODELFILE}" << 'TEMPLATE_END'
# Oracle CNE Fine-tuned Model
# Based on Llama 3.1 8B Instruct, fine-tuned on Oracle CNE documentation

FROM ./Model/oracle_cne_merged_16bit

SYSTEM """You are an expert on Oracle Cloud Native Environment (CNE). Provide accurate, detailed, and helpful answers based on the official Oracle CNE documentation. Include specific commands, configuration details, and best practices when relevant."""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER stop <|eot_id|>
PARAMETER stop <|end_of_text|>
TEMPLATE_END
fi

echo "Modelfile created at ${MODELFILE}"

# --- Import into Ollama ---

echo ""
echo "Importing model into Ollama as '${MODEL_NAME}'..."
if [[ -z "${GGUF_FILE}" ]]; then
    echo "This will convert safetensors to GGUF and quantize automatically."
fi
echo "This may take several minutes depending on your machine."
echo ""

ollama create "${MODEL_NAME}" -f "${MODELFILE}"

echo ""
echo "Done! Model imported as '${MODEL_NAME}'."
echo ""
echo "Run it with:"
echo "  ollama run ${MODEL_NAME}"
echo ""
echo "Example:"
echo "  ollama run ${MODEL_NAME} \"How do I create a Kubernetes cluster with ocne?\""
