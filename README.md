# Anamnesis

> **A CLI companion that gives your codebase a long-term memory, so every AI-assisted coding session starts smart instead of starting blank.**

[![Powered By Cognee AI](https://img.shields.io/badge/Powered%20By-Cognee%20AI-6510F4?style=for-the-badge)](https://cognee.ai)
[![Local & Free via Ollama](https://img.shields.io/badge/LLM-Local%20%26%20Free%20(Ollama)-000000?style=for-the-badge)](https://ollama.com)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](#11-license)

---

## 🏆 Built for the Cognee AI Hackathon

Anamnesis is a **codebase memory infrastructure showcase** built on **[Cognee AI](https://cognee.ai)**. Rather than treating Cognee as a basic vector database, it exercises the full **Cognee Memory Lifecycle** — and runs **100% locally and free** using [Ollama](https://ollama.com) (no paid API keys required).

```
                  ┌───────────────────────────────────────────────┐
                  │          Cognee Memory Lifecycle Engine       │
                  └───────────────────────┬───────────────────────┘
                                          │
    ┌───────────────────────┬─────────────┴─────────┬───────────────────────┐
    ▼                       ▼                       ▼                       ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  remember()   │   │   recall()    │   │   memify()    │   │   forget()    │
│  ingests git  │   │ pre-commit    │   │ consolidates  │   │ decays dead   │
│ history & bugs│   │ graph query   │   │  team rules   │   │ code memory   │
└───────────────┘   └───────────────┘   └───────────────┘   └───────────────┘
```

| Cognee Primitive | Implementation | CLI Command |
|---|---|---|
| **`remember()`** | Ingests git commit diffs, bug root causes, and architecture decisions into the graph | `anamnesis remember-bug`<br>`anamnesis remember` |
| **`recall()`** | Hybrid graph traversal + vector search to surface contextual warnings | `anamnesis ask`<br>`anamnesis timeline`<br>Git pre-commit hook |
| **`memify()`** | Clusters near-duplicate bug reports into generalized team coding conventions | `anamnesis reflect`<br>`anamnesis rules` |
| **`improve()`** | Re-indexes graph relationships, adapts edge weights, and enriches nodes | `anamnesis improve`<br>`anamnesis feedback` |
| **`forget()`** | Decays stale memory nodes when code is deleted or refactored | `anamnesis forget` |

---

## 1. The Problem

Every AI coding assistant today suffers from **amnesia**. You fix a subtle race condition or null pointer bug in `user_service.py` on Monday. On Friday, a teammate (or you, on a different feature branch) writes the exact same flaw in `payment_service.py`. The assistant has no idea it already saw this pattern, because LLM context resets every session and lives in isolated chat windows.

The true knowledge of a codebase — *why architectural decisions were made, what broke last time someone touched a module, and which conventions the team quietly enforces* — lives scattered across closed GitHub issues, old PR comments, Slack threads, or a senior engineer's head. None of it is queryable at the exact moment a developer is about to repeat the same mistake.

---

## 2. The Idea: Codebase Memory Infrastructure

**Anamnesis** sits next to your standard git workflow and builds a **persistent, evolving knowledge graph** of your codebase using **[Cognee AI](https://cognee.ai)**. It watches git commits, ingests bug fixes and their root causes, and surfaces contextual warnings before a commit is finalized.

It exercises the full **Cognee Memory Lifecycle**:
1. **Remember** — Ingest git history, bug root causes, and architectural decisions into graph/vector memory.
2. **Recall** — Query the graph before committing or on-demand via natural language Q&A.
3. **Memify / Reflect** — Consolidate recurring bug patterns across files into team-wide coding rules.
4. **Improve** — Optimize memory weights and relationship edges post-ingestion.
5. **Forget** — Surgically decay or prune stale memories when code is refactored or deleted.

---

## 3. Architecture

```
┌───────────────────────────────────────┐
│          Git Repository (Local)       │
│      commits / diffs / staged files   │
└───────────────────┬───────────────────┘
                    │ Git hook (.git/hooks/pre-commit)
                    ▼
┌───────────────────────────────────────┐
│          Anamnesis CLI (Python)       │
│    Typer commands + Rich UI + MCP     │
│  init · remember-bug · ask · reflect  │
│  visualize · timeline · forget · …    │
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│           Cognee Memory Layer         │
│   remember / recall / memify / forget │
│   (Graph DB + Vector store engine)    │
└───────────────────┬───────────────────┘
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
┌───────────────────┐  ┌───────────────────┐
│   Ollama (local)  │  │  OpenAI / Cognee  │
│  llama3.1:8b +    │  │  Cloud (optional) │
│  nomic-embed-text │  │                   │
└───────────────────┘  └───────────────────┘
```

**Local JSON store as ground truth.** Every memory is also written to `.anamnesis/memories.json`. If Cognee/embeddings are ever unavailable, recall gracefully falls back to local keyword scoring, so the CLI never hard-fails.

---

## 4. Quickstart & Installation

### Prerequisites
- **Python 3.10+** and **Git**
- **[Ollama](https://ollama.com/download)** for the default local, free LLM + embeddings backend

### Step 1 — Install Anamnesis

```bash
git clone https://github.com/your-username/Anamnesis.git
cd Anamnesis

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Step 2 — Set up the local LLM backend (Ollama)

Anamnesis defaults to running everything locally and free via Ollama — no OpenAI key needed.

```bash
# 1. Install Ollama:  https://ollama.com/download   (or: brew install ollama)
# 2. Start the server (keep it running):
ollama serve

# 3. Pull the models (one-time, ~5 GB total):
ollama pull llama3.1:8b        # chat / entity extraction
ollama pull nomic-embed-text   # embeddings
```

> The `transformers` package (installed via `requirements.txt`) is required — Cognee's local Ollama embedder uses a HuggingFace tokenizer for token counting.

### Step 3 — Initialize in your target repo

```bash
anamnesis init
```
*Ingests recent git commit history into Cognee memory and installs the Git pre-commit hook.*

### Step 4 — Try it

```bash
anamnesis remember-bug \
  --file "services/user_service.py" \
  --title "NullPointerException in fetch_user_profile" \
  --cause "Unchecked response.json() on 204 status" \
  --fix "Added HTTP status check and defensive .get() chaining"

anamnesis ask "null pointer api response"
anamnesis visualize
```

---

## 5. Configuration

Configuration lives in `.anamnesis/config.json` (per-repo) with environment overrides from `.env`. **Environment variables always win**, so `.env` overrides `config.json`.

### LLM / embedding backend

| Setting (`config.json`) | Default | Purpose |
|---|---|---|
| `llm_provider` | `ollama` | Backend provider: `ollama` (local & free), `llama_cpp` (quantized local GGUF), or `openai` (paid) |
| `llm_backend` | `llama_cpp` | Target engine for local quantized models |
| `llm_model` | `llama3.1:8b` | Chat / entity-extraction model name or identifier |
| `model_path` | `null` | Absolute or relative path to a local quantized `.gguf` model file |
| `model_quantization` | `Q4_K_M` | Precision level: `Q2_K`, `Q3_K`, `Q4_K_M`, `Q5_K_M`, `Q8_0` |
| `context_tokens` | `4096` | Context window size in tokens |
| `max_batch_size` | `512` | Batch size for prompt evaluation |
| `n_gpu_layers` | `35` | Number of model layers offloaded to GPU/Metal |
| `threads` | `8` | Number of CPU threads used for inference |
| `memory_budget_mb` | `4096` | Runtime memory limit (MB) to prevent OOM on constrained machines |
| `coreml_enabled` | `false` | Enable Apple Metal & CoreML hardware acceleration on macOS |
| `coreml_compute_units` | `ALL` | CoreML compute unit target (`ALL`, `CPU_AND_GPU`, `CPU_ONLY`) |
| `use_mlock` | `true` | Lock model into RAM to prevent memory swapping |
| `use_mmap` | `true` | Memory-map model file for fast loading |
| `embedding_model` | `nomic-embed-text` | Embedding model |
| `embedding_dimensions` | `768` | Embedding vector size |
| `ollama_base_url` | `http://localhost:11434/v1` | Ollama endpoint |
| `use_custom_graph_schema` | `false` | Use the typed `CodeKnowledgeGraph` schema (needs a strong LLM) |
| `use_temporal_cognify` | `false` | Track bug-pattern evolution over time (needs a strong LLM) |
| `reflection_threshold` | `3` | Auto-consolidate rules after every N bug fixes |

> **Why the graph flags default off:** the typed `CodeFile → Function → BugPattern → Fix` schema and temporal event extraction require an LLM that reliably emits strict structured JSON. Small local models (e.g. `llama3.2:3b`) can't, so Anamnesis uses Cognee's robust built-in extraction by default and gracefully falls back if the typed schema fails. Turn both flags on with a strong model (OpenAI, or a large local model) to get the richer typed graph.

### LLM Backends

Anamnesis supports three first-class LLM backends:

1. **`ollama`** (Default) — fully local and free, connects to a local Ollama daemon.
2. **`llama_cpp`** — fully local, zero-daemon quantized inference with GGUF files, Apple Metal / CoreML acceleration, and strict memory budgeting.
3. **`openai`** — remote cloud inference using standard OpenAI API keys.

---

### Local Quantized Inference via `llama.cpp`

For maximum efficiency and offline operation without background server daemons, Anamnesis supports local quantized inference via `llama.cpp`.

#### 1. Setup `llama-cpp-python`

Standard installation:
```bash
pip install llama-cpp-python
```

**macOS with Apple Silicon (Metal & CoreML acceleration):**
```bash
CMAKE_ARGS="-DGGML_METAL=ON -DGGML_METAL_EMBEDDING=ON -DGGML_METAL_USE_BF16=ON" \
pip install llama-cpp-python --upgrade --force-reinstall
```

#### 2. Quantization Overview

Quantization compresses model weights from 16-bit floating point down to 2–8 bits, dramatically reducing RAM usage and enabling fast local execution:

| Quantization | Relative Size | Quality Retention | Recommended Use Case |
|---|---|---|---|
| **`Q2_K`** | ~30% of fp16 | Low | Ultra-constrained devices (< 4 GB RAM) |
| **`Q3_K`** | ~40% of fp16 | Moderate | Low-RAM systems (< 6 GB RAM) |
| **`Q4_K_M`** *(Default)* | ~50% of fp16 | Very High (~99% perplexity) | **Best balance** of speed, memory, and reasoning |
| **`Q5_K_M`** | ~60% of fp16 | Near Lossless | When memory permits (8 GB - 16 GB RAM) |
| **`Q8_0`** | ~80% of fp16 | Lossless | Highest precision, requires 12 GB+ RAM |

#### 3. Memory Budget Tuning & Safe Fallbacks

Local models can be memory-heavy. Anamnesis introduces explicit memory budgeting via `memory_budget_mb`:
- **Conservative target for 7B/8B Q4 models on Apple Silicon:** 4096 MB – 8192 MB RAM.
- **Adaptive parameters:** When memory constraints are tight (e.g. < 2048 MB), Anamnesis automatically scales down `context_tokens` (from 4096 to 2048/1024), reduces `max_batch_size`, and adjusts `n_gpu_layers` to protect against out-of-memory (OOM) crashes.
- **Safe fallback:** If `llama_cpp` is selected but the package is not installed or the model file is not found, Anamnesis surfaces clear actionable diagnostics and falls back safely to smart pattern analysis.

#### 4. Example `.env` for `llama.cpp`

```env
LLM_PROVIDER=llama_cpp
LLM_MODEL=llama-3.1-8b-instruct-q4_k_m.gguf
MODEL_PATH=/models/llama-3.1-8b-instruct-q4_k_m.gguf
MODEL_QUANTIZATION=Q4_K_M
CONTEXT_TOKENS=4096
MAX_BATCH_SIZE=512
N_GPU_LAYERS=35
THREADS=8
MEMORY_BUDGET_MB=4096
COREML_ENABLED=true
COREML_COMPUTE_UNITS=ALL
USE_MLOCK=true
USE_MMAP=true
```

### Example `.env` (local Ollama — the default)

```env
# LLM + embeddings: local & free via Ollama
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b
LLM_ENDPOINT=http://localhost:11434/v1
LLM_API_KEY=ollama

EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
# NOTE: /api/embed (batch API), NOT /api/embeddings
EMBEDDING_ENDPOINT=http://localhost:11434/api/embed
EMBEDDING_DIMENSIONS=768
HUGGINGFACE_TOKENIZER=nomic-ai/nomic-embed-text-v1.5

# Raw OpenAI-SDK calls (diff summaries, rule clustering) route to Ollama too
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
```

### Optional: OpenAI or Cognee Cloud

```bash
# Use a paid OpenAI key instead of Ollama
anamnesis config set-llm-key <your_openai_key>   # then set llm_provider=openai

# Team-wide shared memory via Cognee Cloud (platform.cognee.ai)
anamnesis config set-cloud-key <your_cognee_api_key>
```

---

## 6. CLI Command Reference

### `anamnesis init`
Ingests commit history into Cognee memory and installs `.git/hooks/pre-commit`.
```bash
anamnesis init
```

### `anamnesis remember-bug`
Logs a bug fix, its root cause, and fix details into codebase memory. Supports explicit flags or auto-summarization from the staged `git diff`.
```bash
anamnesis remember-bug --file services/user_service.py \
  --title "Unchecked API crash" --cause "Missing null check" --fix "Added guard clause"

anamnesis remember-bug --auto   # summarize the staged diff
```

### `anamnesis remember`
Ingests a general document, ADR, or PR note into the knowledge graph.
```bash
anamnesis remember "Use the service layer for DB queries" \
  --content "All direct DB queries must pass through services." --file services/base.py
```

### `anamnesis ask`
Query codebase memory in natural language (GRAPH_COMPLETION + HYBRID_COMPLETION + CODING_RULES). Shows which strategy found each result.
```bash
anamnesis ask "Why do we validate external API responses in the service layer?"
```

### `anamnesis timeline`
Temporal recall — shows how bug patterns evolved over time (requires `use_temporal_cognify`; falls back to local timestamp ordering otherwise).
```bash
anamnesis timeline "recurring null pointer bugs" --top-k 10
```

### `anamnesis reflect`
Clusters related bug reports across files into consolidated team rules (`memify`).
```bash
anamnesis reflect
```

### `anamnesis rules`
Displays a Rich table of all active consolidated team rules and their provenance links.
```bash
anamnesis rules
```

### `anamnesis improve`
Post-ingestion graph enrichment, edge-weight adaptation, and node optimization.
```bash
anamnesis improve
```

### `anamnesis feedback`
Rate the last recall result to improve future ranking (Cognee truth-subspace reranking).
```bash
anamnesis feedback --helpful
anamnesis feedback --not-helpful
```

### `anamnesis forget`
Decays or removes stale memory by ID or file path.
```bash
anamnesis forget mem_bug_8cec331b
anamnesis forget services/user_service.py
```

### `anamnesis visualize`
Opens an **interactive provenance graph** in your browser (D3 force graph). Merges the Cognee provenance graph (User → Dataset → File → Session) with your local memory records, so **clicking any node opens a detail panel** with the bug's type, root cause, fix, and file. Nodes use short tags; the graph supports zoom, pan, and drag.
```bash
anamnesis visualize                 # open in browser
anamnesis visualize -o graph.html   # save to a file instead
```

### `anamnesis status`
Dashboard of memory statistics, active rule counts, and Git hook status.
```bash
anamnesis status
```

### `anamnesis config`
Manage LLM provider, quantized inference, and Cognee Cloud settings.
```bash
anamnesis config show                              # active configuration dashboard
anamnesis config set-backend llama_cpp             # set backend: ollama | openai | llama_cpp
anamnesis config set-model /path/to/model.gguf     # configure local GGUF model path or name
anamnesis config set-quantization Q4_K_M           # configure GGUF quantization level
anamnesis config set-context 4096                  # configure context window (tokens)
anamnesis config set-memory-budget 4096            # configure runtime memory limit (MB)
anamnesis config set-llm-key <openai_key>          # configure a paid LLM key
anamnesis config set-cloud-key <cognee_key>        # configure Cognee Cloud
```

### `anamnesis mcp-serve`
Runs Anamnesis as an **MCP server** so Claude Code / Cursor can use codebase memory as native tools (`recall_codebase_memory`, `remember_bug_fix`, `get_coding_rules`, `get_memory_status`, `forget_memory`).
```bash
anamnesis mcp-serve                       # stdio (default)
anamnesis mcp-serve -t http --port 8765   # HTTP transport
```
Claude Desktop config (`~/.claude/claude_desktop_config.json`):
```json
{ "mcpServers": { "anamnesis": { "command": "anamnesis", "args": ["mcp-serve"] } } }
```

---

## 7. Visualizing the Memory Graph

`anamnesis visualize` renders an interactive graph of everything Anamnesis knows:

- **Nodes** — `user`, `dataset`, `doc`, `session` (from Cognee provenance) plus your `bug_fix`, `rule`, `commit`, and `documentation` memories, color-coded by type with a legend.
- **Click a node** → a side panel shows structured detail:
  ```
  Type: bug_fix
  Root Cause: Unchecked response.json() on 204 status
  Fix: Added HTTP status check and defensive .get() chaining
  File: services/user_service.py
  ```
- **Interactions** — scroll to zoom, drag the background to pan, drag nodes to reposition.

The page is a self-contained HTML file, so you can also commit or share `graph.html`.

---

## 8. Live Interactive Demo

Run the self-contained demo to watch all 5 Cognee primitives in action:

```bash
python demo/run_demo.py
```

It ingests baseline history, logs a bug (`remember`), fires a pre-commit warning on a similar flaw (`recall`), consolidates rules (`memify/reflect`), decays stale memory (`forget`), and answers a natural-language query (`ask`).

---

## 9. How It Works (Internals)

- **`anamnesis/cli.py`** — Typer CLI + Rich UI, including the D3 graph renderer for `visualize`.
- **`anamnesis/config.py`** — config loading and `configure_llm_env()`, which wires Cognee/LiteLLM and the OpenAI SDK to the chosen provider (Ollama by default).
- **`anamnesis/memory/client.py`** — `MemoryClient`: the Cognee integration and local JSON store, with robust cognify fallback for weak local models.
- **`anamnesis/memory/consolidator.py`** — bug-pattern clustering into team rules.
- **`anamnesis/git/`** — commit inspection and pre-commit hook installation.
- **`anamnesis/mcp_server.py`** — MCP server exposing memory as tools.

---

## 10. Running Tests

```bash
pytest tests/
```

---

## 11. License

Licensed under the **MIT License**.
