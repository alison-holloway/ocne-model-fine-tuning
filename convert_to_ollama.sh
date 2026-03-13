#!/bin/bash
#
# Import the fine-tuned Oracle CNE model into Ollama.
#
# Preferred path: supply a pre-quantized GGUF file (export via llama.cpp — see plan.md).
# This is the recommended approach — lightweight import, no heavy RAM conversion.
#
# Fallback: if no GGUF file is found, uses the merged 16-bit safetensors model.
# Ollama will convert and quantize it automatically, which requires ~32 GB RAM.
#
# Prerequisites:
#   curl -fsSL https://ollama.com/install.sh | sh
#   ollama serve  (in another terminal, or: sudo systemctl start ollama)
#
# Usage:
#   ./convert_to_ollama.sh              # auto-detect GGUF or safetensors
#   ./convert_to_ollama.sh --16bit      # force safetensors conversion
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
    echo "Install with: curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

if ! ollama list &> /dev/null 2>&1; then
    echo "Error: ollama is not running."
    echo "Start it with: ollama serve"
    echo "Or as a service: sudo systemctl start ollama"
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
        echo "  - Model/*.gguf                      (recommended — export via llama.cpp)"
        echo "  - Model/oracle_cne_merged_16bit/    (safetensors — needs ~32 GB RAM to convert)"
        echo ""
        echo "To produce the merged model, re-train with:"
        echo "  python train.py --merge"
        echo ""
        echo "To export GGUF from the merged model (see plan.md for full instructions):"
        echo "  git clone https://github.com/ggerganov/llama.cpp"
        echo "  cd llama.cpp"
        echo "  cmake -B build && cmake --build build --config Release"
        echo "  python3 -m venv venv-llamacpp && source venv-llamacpp/bin/activate"
        echo "  pip install -r requirements.txt"
        echo "  python3 convert_hf_to_gguf.py ../ocne-model-training/Model/oracle_cne_merged_16bit \\"
        echo "    --outfile ../ocne-model-training/Model/oracle_cne_f16.gguf --outtype f16"
        echo "  ./build/bin/llama-quantize \\"
        echo "    ../ocne-model-training/Model/oracle_cne_f16.gguf \\"
        echo "    ../ocne-model-training/Model/oracle_cne_q4_k_m.gguf Q4_K_M"
        exit 1
    fi

    echo "WARNING: No GGUF file found in Model/. Falling back to safetensors conversion."
    echo "Ollama will convert and quantize automatically — this requires ~32 GB RAM."
    echo ""
    echo "For a faster, lower-memory import, export a GGUF first (see plan.md)."
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

echo "Modelfile written to ${MODELFILE}"

# --- Import into Ollama ---

echo ""
echo "Importing model into Ollama as '${MODEL_NAME}'..."
if [[ -z "${GGUF_FILE}" ]]; then
    echo "Converting safetensors to GGUF and quantizing — this may take several minutes."
fi
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
