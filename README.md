# Colony

Colony is a high-performance model orchestration system designed for Boksburg Celeron hardware (1.2GB RAM limit). It features a decentralized memory (Nest), a voting-based router (Council), and an evolutionary learning loop.

## Core Architecture

- **Nest (Memory)**: HybridRAG (Vector + Graph) with exponential forgetting curves.
- **Council (Routing)**: STV (Single Transferable Vote) election using Satellites (York, Lilith, Atlas).
- **York (RAM Governor)**: Hard-authority resource management (85% block, 92% unload).
- **Scout (Triage)**: Bonsai-1.7B Q4 urgency scoring + direct Nest answers. Always loaded, <50ms latency.
- **Evolution**: LoRA spawning (Drones) and distillation (Raids) judged by Valkyrie.

## Components

- `instruct/`: OpenAI-compatible FastAPI and Python CLI.
- `core/`: Deep domain modules for Routing, Memory, Evolution, and Scout.
- `core/workers/scout.py`: Scout implementation — urgency scoring, direct Nest answers.
- `core/workers/loader.py`: Worker model loading with York RAM enforcement.
- `models/`: Domain entities and dataclasses.

## Getting Started

1. Initialize Nest: `colonyctl status`
2. Submit task: `colonyctl task "write async sleep"`
3. Monitor RAM: `colonyctl york --watch`

See `UBIQUITOUS_LANGUAGE.md` for the project glossary.
