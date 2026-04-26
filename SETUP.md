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

- **Scout**: TODO (Bonsai-8B is full model; Scout may be separate small model later)
- **Worker**: Loads `Bonsai-8B-Q1_0.gguf` via internal llama.cpp binding (not yet implemented)
- **RAM**: With Bonsai (1.15GB), York will block if any other memory consumer runs. Ensure baseline < 50MB.

## 9. TODO (Not Implemented Yet)

- RLM integration (`rlm` Python package)
- NestREPL sandbox
- Actual Bonsai model loading in `WorkerLoader`

**See `instruct/*.md` for architectural specs.**
