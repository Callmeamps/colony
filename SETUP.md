# Colony Setup Guide

Boksburg deployment: 1.2GB RAM limit.

## 1. Prerequisites

- Python 3.11+
- Redis 7
- MongoDB 6
- Git
- CCompiler (gcc/clang) for llama.cpp

## 2. Clone Dependencies

### PrismML llama.cpp (Q1_0 support)
```
git clone https://github.com/PrismML-Eng/llama.cpp
cd llama.cpp
cmake -B build -DGGML_CUDA=ON -DGGML_METAL=ON
cmake --build build -j
```

### Bonsai Models
Download from HuggingFace:
- Bonsai-8B Q1_0: `https://huggingface.co/prism-ml/Bonsai-8B-gguf`
- Bonsai-1.7B Q4: `https://huggingface.co/prism-ml/Bonsai-1.7B-gguf` (Scout)
- Place in `./models/` directory.

### Python Packages
```
uv pip install fastapi uvicorn[standard] redis pymongo pyyaml typer[all] rich psutil cognee lancedb networkx
```

## 3. Database Setup

```bash
# Redis (default)
redis-server

# MongoDB (default)
mongod --dbpath ./data/mongo
```

## 4. Colony Directories

```
mkdir -p nest/lancedb nest/meta.db models scripts
```

## 5. Configuration

Create `~/.config/colony/config.yaml`:
```yaml
redis_url: redis://localhost:6379/0
mongo_url: mongodb://localhost:27017
api_url: http://localhost:7777
default_stream: true
timeout_s: 30
```

## 6. Launch API

```bash
uvicorn instruct.colony_api_main:app --host 127.0.0.1 --port 7777
```

## 7. Verify

```bash
# Health check
curl http://localhost:7777/v1/models
colonyctl status
colonyctl task "test"
```

## 8. Model Setup Notes

- **Scout**: `Bonsai-1.7B-Q4_0.gguf` (~200MB disk, ~250MB RAM). Always loaded, never unloaded. See `core/workers/scout.py`. Functions: urgency scoring, direct Nest answers (cosine >0.85 threshold).
- **Worker**: Loads `Bonsai-1.7B-Q4_0.gguf` via llama.cpp Python bindings (IMPLEMENTED in `core/workers/loader.py`)
- **RAM**: With Bonsai-1.7B (~300MB including overhead), system has more headroom. York blocks at 85% dynamic threshold.

### Download Model
```bash
# Download Bonsai-1.7B Q4_0 from HuggingFace
cd models/
wget https://huggingface.co/prism-ml/Bonsai-1.7B-gguf/resolve/main/bonsai-1.7b-q4_0.gguf
# Verify
ls -lh bonsai-1.7b-q4_0.gguf  # Should be ~200MB
```

### Model Config
Model manifest at `models/bonsai-1.7b-q4_0.gguf.json`

## 9. Verified Features

- ✅ RLM integration (`rlms` Python package) - Council uses RLM for recursive routing
- ✅ NestREPL sandbox - Safe exec/eval with tool registry
- ✅ Actual Bonsai model loading in `WorkerLoader` - Uses llama.cpp Python bindings
- ✅ York dynamic thresholds - Block at 85% based on loaded model RAM

**See `instruct/*.md` for architectural specs.**
