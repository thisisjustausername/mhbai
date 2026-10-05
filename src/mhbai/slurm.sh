#!/bin/bash -l
#SBATCH --gres=gpu:1
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --job-name=vllm_test
#SBATCH --output=logs/%x-%j.out
#SBATCH --error=logs/%x-%j.err

./cuda_application

uv venv venv
source venv/bin/activate
uv pip3 install -r requirements.txt

# Activate environment
source ~/.bashrc
conda activate myenv

# Config
MODEL="meta-llama/Llama-3-8B-Instruct"
PORT=8000
HOST=127.0.0.1

echo "Starting vLLM server..."

python -m vllm.entrypoints.openai.api_server \
    --model $MODEL \
    --host $HOST \
    --port $PORT \
    > vllm.log 2>&1 &

VLLM_PID=$!

echo "vLLM PID: $VLLM_PID"

# Cleanup function
cleanup() {
    echo "Stopping vLLM..."
    kill $VLLM_PID
}

trap cleanup EXIT

echo "Waiting for vLLM to become ready..."

# Wait until server responds
until curl -s http://$HOST:$PORT/v1/models > /dev/null; do
    sleep 2
done

echo "vLLM is ready."

# Run your script
python query_script.py --port $PORT

echo "Done."
