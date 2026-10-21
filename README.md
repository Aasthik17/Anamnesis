# Anamnesis

> **Continuous, long-term codebase memory infrastructure for developer workflows and AI coding agents.**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Architecture: Hybrid Graph + Vector](https://img.shields.io/badge/Architecture-Hybrid%20Graph%20%2B%20Vector-6510F4?style=flat-square)](https://cognee.ai)
[![Local Inference: llama.cpp / Ollama](https://img.shields.io/badge/Inference-Local%20%26%20Private%20(GGUF%20%2F%20Ollama)-000000?style=flat-square)](https://github.com/ggerganov/llama.cpp)
[![MCP Compatible](https://img.shields.io/badge/Protocol-MCP%20Enabled-blueviolet?style=flat-square)](https://modelcontextprotocol.io)
[![Tests: Pytest Passed](https://img.shields.io/badge/Tests-Passing-brightgreen?style=flat-square)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

---

## Overview

Modern AI coding assistants suffer from **session amnesia**. Context windows reset between sessions, while critical engineering decisions, subtle bug root causes, and architectural lessons remain trapped across ephemeral chat windows, closed pull requests, and fragmented team discussions. When a developer or AI agent edits related services weeks later, identical bugs and anti-patterns are frequently reintroduced.

**Anamnesis** solves this fundamental disconnect by providing a persistent, evolving **codebase knowledge graph** that sits alongside your standard Git workflow. It transforms transient code modifications and post-mortems into queryable long-term memory. 

Whether operated as an automated Git pre-commit guard, a terminal CLI, or a native **Model Context Protocol (MCP)** server for AI IDEs like Claude Code and Cursor, Anamnesis ensures that every coding session starts with full historical context.

---

## Key Highlights

- **Full Memory Lifecycle Engine**: Implements end-to-end memory management:
  - `remember`: Structured ingestion of Git diffs, bug post-mortems, and architectural decision records (ADRs).
  - `recall`: Hybrid graph traversal + vector retrieval surfaced at commit time or on-demand.
  - `memify`: Unsupervised clustering that consolidates recurring bug patterns into team-wide architectural rules.
  - `improve`: Dynamic edge-weight adaptation and graph enrichment.
  - `forget`: Surgical memory decay and pruning for deleted or refactored components.
- **Context-Aware Git Pre-Commit Hook**: Analyzes staged diffs against historical bug memories to flag regressions and suggest validated fixes before changes are committed.
- **Native Model Context Protocol (FastMCP)**: Directly exposes codebase memory tools (`recall_codebase_memory`, `remember_bug_fix`, `get_coding_rules`) to modern AI agents (Cursor, Claude Code, Windsurf).
- **100% Local & Privacy-First Execution**: Zero telemetry and zero required external API dependencies. Native support for local quantized inference via `llama.cpp` (GGUF with Apple Metal / CoreML hardware acceleration) and Ollama, alongside optional OpenAI backends.
- **Dual-Layer Fault Resilience**: Ingests into Cognee's hybrid graph/vector store while maintaining a local JSON ground truth. If vector stores or LLM endpoints are unavailable, the system gracefully falls back to local lexical scoring without disrupting developer flow.
- **Interactive Knowledge Graph Visualizer**: Built-in D3.js force-directed visualization to explore relationships between files, commits, bug patterns, and synthesized rules with interactive metadata inspection.

---

## System Architecture

```
                                  DEVELOPER WORKSPACE
       ┌───────────────────────────────┬───────────────────────────────┐
       │                               │                               │
       ▼                               ▼                               ▼
  [Git Workflow]               [Terminal CLI]                   [AI Agents / IDE]
  Staged Diffs & Hooks         Typer + Rich Engine              Cursor, Claude Code (MCP)
       │                               │                               │
       └───────────────────────┬───────┴───────────────────────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │         ANAMNESIS CORE        │
               │ ───────────────────────────── │
               │ • Git Inspector & Pre-Commit  │
               │ • Pattern Consolidator Engine │
               │ • Memory Client & Fallback    │
               │ • FastMCP Server Interface    │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │    HYBRID MEMORY SUBSYSTEM    │
               │ ───────────────────────────── │
               │ • Cognee Graph + Vector Store │
               │ • Typed Code Ontology Schemas │
               │ • Local JSON Ground Truth     │
               └───────────────┬───────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
    [Local Private Inference]       [Cloud Providers]
    • llama.cpp (GGUF / Metal)      • OpenAI API
    • Ollama (llama3.1 / nomic)     • Cognee Cloud
```

### Memory Lifecycle Walkthrough

| Lifecycle Stage | Underlying Mechanism | CLI Interface |
|---|---|---|
| **`remember()`** | Extracts entities (affected files, error patterns, root causes) and maps them into graph nodes and vector embeddings. | `anamnesis remember-bug`<br>`anamnesis remember` |
| **`recall()`** | Executes hybrid retrieval (graph neighbor expansion + dense vector similarity) to surface contextual warnings. | `anamnesis ask`<br>`anamnesis timeline`<br>Git pre-commit hook |
| **`memify()`** | Clusters cross-file incidents using semantic similarity to formulate generalized engineering guidelines. | `anamnesis reflect`<br>`anamnesis rules` |
| **`improve()`** | Re-indexes relational edges, recalculates node centrality, and applies feedback weighting. | `anamnesis improve`<br>`anamnesis feedback` |
| **`forget()`** | Decays confidence scores or removes orphaned memory nodes when codebases undergo major refactoring. | `anamnesis forget` |

---

## Technical Stack

| Layer | Technologies |
|---|---|
| **Core Runtime** | Python 3.10+, Typer, Pydantic V2, Rich |
| **Knowledge Graph & Memory** | Cognee, NetworkX, Vector Indexing, Hybrid Graph-Vector Traversal |
| **Local LLM Engine** | `llama.cpp` (GGUF, Metal/CoreML acceleration), Ollama |
| **Developer Integration** | GitPython (Git pre-commit hooks), FastMCP (Model Context Protocol) |
| **Interactive Visualization** | D3.js (Force-directed graph renderer, embedded HTML) |
| **Testing & Quality Assurance** | Pytest, Strict Type Annotations, Defensive Fallback Handlers |

---

## Installation & Setup

### Prerequisites
- **Python 3.10+**
- **Git**
- *(Optional, for local inference)* **[Ollama](https://ollama.com)** or a local `.gguf` model for `llama.cpp`

### 1. Clone & Install

```bash
git clone https://github.com/your-username/Anamnesis.git
cd Anamnesis

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### 2. Configure Your Inference Provider

#### Option A: Local & Free via Ollama (Recommended Default)
```bash
# Pull default models
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# Ensure the Ollama server is running
ollama serve
```

#### Option B: Standalone Quantized GGUF via `llama.cpp`
For single-binary offline operation with zero background daemons and hardware-accelerated inference:
```bash
# For Apple Silicon with Metal & CoreML acceleration
CMAKE_ARGS="-DGGML_METAL=ON -DGGML_METAL_EMBEDDING=ON -DGGML_METAL_USE_BF16=ON" \
pip install llama-cpp-python --upgrade --force-reinstall

# Configure model and hardware parameters
anamnesis config set-backend llama_cpp
anamnesis config set-model /path/to/llama-3.1-8b-instruct-q4_k_m.gguf
anamnesis config set-quantization Q4_K_M
anamnesis config set-memory-budget 4096
```

#### Option C: Cloud Providers (OpenAI)
```bash
anamnesis config set-backend openai
anamnesis config set-llm-key sk-...
```

---

## Quickstart

### Step 1: Initialize Repository Memory
Navigate to any Git project repository and run:
```bash
anamnesis init
```
This inspects recent commit history to establish baseline project context and automatically installs the Git pre-commit hook into `.git/hooks/pre-commit`.

### Step 2: Ingest a Bug Fix
Record a resolved bug, detailing its root cause and remediation pattern:
```bash
anamnesis remember-bug \
  --file "services/user_service.py" \
  --title "Unhandled Empty Response on User Ingestion" \
  --cause "Missing 204 No Content validation prior to response.json() parsing" \
  --fix "Added explicit HTTP status verification and defensive dictionary access"
```
*Tip: You can also run `anamnesis remember-bug --auto` to automatically analyze staged Git diffs with your configured LLM.*

### Step 3: Contextual Querying
Query your codebase's institutional memory using natural language:
```bash
anamnesis ask "Why do we validate API status codes in the service layer?"
```

### Step 4: Rule Synthesis (`memify`)
When multiple related issues are logged across different services, synthesize them into a permanent codebase convention:
```bash
# Consolidate related patterns into high-level rules
anamnesis reflect

# Inspect active team coding conventions
anamnesis rules
```

---

## Advanced Usage & Capabilities

### 1. Automated Git Regression Prevention

Once initialized, Anamnesis runs seamlessly as part of your Git workflow. When a developer stages changes and runs `git commit`, the pre-commit hook:
1. Extracts the staged diff and affected file paths.
2. Performs a similarity search against the knowledge graph.
3. Warns the developer if staged code re-introduces known failure modes:

```
┌── [!] ANAMNESIS REGRESSION WARNING ────────────────────────────────────────┐
│ Staged file: services/payment_service.py                                    │
│ Warning: Similar failure mode previously identified in user_service.py      │
│ Root Cause: Unchecked external response payload causing null dereference.  │
│ Recommended Fix: Enforce status check and fallback defaults prior to read. │
└────────────────────────────────────────────────────────────────────────────┘
```

### 2. AI Editor Integration via Model Context Protocol (MCP)

Anamnesis provides a native MCP server, enabling AI development environments such as **Claude Code**, **Cursor**, and **Windsurf** to access your codebase's memory layer directly.

Start the server:
```bash
# Standard I/O (default for desktop extensions)
anamnesis mcp-serve

# HTTP SSE transport
anamnesis mcp-serve --transport http --port 8765
```

Add to your Claude Desktop config (`~/.claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "anamnesis": {
      "command": "anamnesis",
      "args": ["mcp-serve"]
    }
  }
}
```

**Exposed MCP Tools:**
- `recall_codebase_memory(query)`: Semantically retrieves historical bugs, design decisions, and fixes.
- `remember_bug_fix(file_path, title, root_cause, fix_applied)`: Records new bug post-mortems directly from conversation.
- `get_coding_rules()`: Fetches synthesized team coding rules.
- `get_memory_status()`: Summarizes active memory nodes, rules, and hook configurations.
- `forget_memory(identifier)`: Prunes obsolete memories.

### 3. Interactive Knowledge Graph Visualizer

Generate and inspect an interactive, force-directed graph of all codebase memories, provenance chains, and synthesized rules:

```bash
# Launch interactive graph in your default browser
anamnesis visualize

# Export standalone HTML visualization
anamnesis visualize -o graph.html
```

- **Interactive Navigation**: Drag nodes, zoom, pan, and filter by node classifications (`bug_fix`, `rule`, `commit`, `doc`).
- **Deep Metadata Inspection**: Clicking any node opens a contextual drawer detailing root causes, fixes, affected files, and timestamped provenance.

---

## CLI Command Reference

| Command | Description |
|---|---|
| `anamnesis init` | Initializes repository tracking and installs Git pre-commit hooks. |
| `anamnesis remember-bug` | Records a bug post-mortem (`--auto` flag summarizes staged Git diffs). |
| `anamnesis remember` | Ingests arbitrary architectural documents, ADRs, or technical notes. |
| `anamnesis ask <query>` | Hybrid search query over the codebase memory graph. |
| `anamnesis timeline <query>` | Temporal retrieval showing how specific bug patterns evolved over time. |
| `anamnesis reflect` | Executes memory consolidation to synthesize higher-order team rules. |
| `anamnesis rules` | Displays all active synthesized architectural and coding rules. |
| `anamnesis improve` | Re-indexes relational edges and adapts node confidence weights. |
| `anamnesis feedback` | Records relevance feedback (`--helpful` / `--not-helpful`) to tune future ranking. |
| `anamnesis forget <id/path>` | Surgically decays or deletes stale memories by ID or target file path. |
| `anamnesis visualize` | Generates and displays an interactive D3.js knowledge graph. |
| `anamnesis status` | Displays runtime statistics, memory counts, and hook status. |
| `anamnesis config` | Inspects and updates LLM backends, quantization, and hardware settings. |
| `anamnesis mcp-serve` | Runs the Model Context Protocol (MCP) server for AI editor integration. |

---

## Configuration & Environment

Project configurations are stored in `.anamnesis/config.json` with environment variable overrides from `.env`.

```env
# --- LLM Engine Configuration ---
LLM_PROVIDER=ollama                     # ollama | llama_cpp | openai
LLM_MODEL=llama3.1:8b
LLM_ENDPOINT=http://localhost:11434/v1
LLM_API_KEY=ollama

# --- Embedding Configuration ---
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_ENDPOINT=http://localhost:11434/api/embed
EMBEDDING_DIMENSIONS=768

# --- Quantized llama.cpp Settings (When using llama_cpp provider) ---
MODEL_PATH=/path/to/model.gguf
MODEL_QUANTIZATION=Q4_K_M
MEMORY_BUDGET_MB=4096
CONTEXT_TOKENS=4096
N_GPU_LAYERS=35
COREML_ENABLED=true
```

---

## Project Structure

```
Anamnesis/
├── anamnesis/
│   ├── cli.py               # Typer CLI application, commands & D3 visualizer
│   ├── config.py            # Configuration manager & LLM environment routing
│   ├── llm_runtime.py       # Quantized llama.cpp runtime & memory budgeting
│   ├── mcp_server.py        # Model Context Protocol (FastMCP) server
│   ├── git/
│   │   ├── hooks.py         # Git pre-commit hook installation and lifecycle
│   │   └── inspector.py     # Commit diff parsing and Git repository inspection
│   ├── memory/
│   │   ├── client.py        # Cognee hybrid graph/vector client + JSON fallback
│   │   ├── consolidator.py  # Unsupervised pattern clustering & rule generation
│   │   └── schemas.py       # Pydantic domain models & graph ontology
│   ├── ui/
│   │   └── formatter.py     # Rich terminal output formatting & dashboards
│   └── utils/
│       └── llm_helper.py    # Zero-shot diff summarization & structured prompt helpers
├── demo/
│   └── run_demo.py          # End-to-end simulated lifecycle demonstration
├── tests/
│   ├── test_cli.py          # CLI command suite tests
│   ├── test_llm_runtime.py  # Quantized inference & memory budget test cases
│   └── test_memory.py       # Memory persistence & retrieval tests
├── pyproject.toml           # Package build metadata & entry points
└── requirements.txt         # Core dependencies
```

---

## Verification & Testing

Anamnesis includes an automated test suite covering CLI commands, memory ingestion, fallback mechanisms, and runtime memory allocation:

```bash
# Run full unit and integration test suite
python3 -m pytest
```

---

## Engineering Design Principles

1. **Deterministic Resilience**: LLM APIs fail, local runtimes crash, and network connections drop. Anamnesis guarantees that Git operations are never blocked: if graph or embedding backends encounter errors, execution transparently falls back to local JSON indexing and regex scoring.
2. **Local-First & Privacy Conscious**: Proprietary source code should never be forced into third-party cloud APIs. Anamnesis provides production-grade local quantized execution with Metal/CoreML acceleration and explicit memory limits.
3. **Actionable at the Point of Impact**: Storing documentation in external portals rarely prevents errors. By embedding intelligence directly into Git pre-commit hooks and AI IDE contexts via MCP, warnings appear at the exact moment code is authored.

---

## License

This project is licensed under the [MIT License](LICENSE).
