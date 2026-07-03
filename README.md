# 🧠 Anamnesis

> **A CLI companion that gives your codebase a long-term memory, so every AI-assisted coding session starts smart instead of starting blank.**

[![Cognee Memory Layer](https://img.shields.io/badge/Powered%20By-Cognee%20AI-6510F4?style=for-the-badge)](https://cognee.ai)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

## 🏆 Built for Cognee AI Hackathon

Anamnesis was designed from the ground up as a **pure memory infrastructure showcase** built on **[Cognee AI](https://cognee.ai)**. Rather than treating Cognee as a basic vector database, Anamnesis exercises all 5 core primitives in the **Cognee Memory Lifecycle**:

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

| Cognee Primitive | Hackathon Showcase Implementation | CLI Command |
|---|---|---|
| **`remember()`** | Ingests git commit diffs, bug root causes, and architecture decisions into the graph | `anamnesis remember-bug`<br>`anamnesis remember` |
| **`recall()`** | Hybrid graph traversal + vector search to surface contextual pre-commit warnings | `anamnesis ask`<br>Git pre-commit hook |
| **`memify()`** | Clusters near-duplicate bug reports into generalized team coding conventions | `anamnesis reflect`<br>`anamnesis rules` |
| **`improve()`** | Re-indexes graph relationships, optimizes edge weights, and enriches nodes | `anamnesis improve` |
| **`forget()`** | Decays stale memory nodes when code is deleted or refactored | `anamnesis forget` |

---

## 🎬 Demo Video & Recording Script

[![Anamnesis Live Demo Video](https://img.youtube.com/vi/YOUR_YOUTUBE_ID/maxresdefault.jpg)](https://www.youtube.com/watch?v=YOUR_YOUTUBE_ID)
> 📹 *Click the image above to watch the 2-minute demonstration of Anamnesis and Cognee AI memory primitives.*
> 
> 📖 **Recording Script & Guide**: See [`DEMO_VIDEO_GUIDE.md`](file:///Users/aasthikupadhyay/Desktop/Anamnesis/DEMO_VIDEO_GUIDE.md) for the scene-by-scene voiceover script, terminal setup, and automated demo runner instructions.

---

## 1. The Problem

Every AI coding assistant today suffers from **amnesia**. You fix a subtle race condition or null pointer bug in `user_service.py` on Monday. On Friday, a teammate (or you, on a different feature branch) writes the exact same flaw in `payment_service.py`. The assistant has no idea it already saw this pattern, because LLM context resets every session and lives in isolated chat windows.

The true knowledge of a codebase—*why architectural decisions were made, what broke last time someone touched a module, and which conventions the team quietly enforces*—lives in scattered places: closed GitHub issues, old PR comments, Slack threads, or a senior engineer's head. None of it is queryable at the exact moment a developer is about to commit the same mistake again.

---

## 2. The Idea: Codebase Memory Infrastructure

**Anamnesis** sits next to your standard git workflow and builds a **persistent, evolving knowledge graph** of your codebase using **[Cognee AI](https://cognee.ai)**. It watches git commits, ingests bug fixes and their root causes, and surfaces contextual warnings before a commit is finalized.

Unlike generic autocomplete or static search indices, Anamnesis exercises the full **Cognee Memory Lifecycle**:
1. **Remember**: Ingest git history, bug root causes, and architectural decisions into graph/vector memory.
2. **Recall**: Query the graph before committing or on-demand via natural language Q&A.
3. **Memify / Reflect**: Consolidate recurring bug patterns across files into team-wide coding rules.
4. **Improve**: Optimize memory weights and relationship edges post-ingestion.
5. **Forget**: Surgically decay or prune stale memories when code is refactored or deleted.

---

## 3. Why Cognee, Specifically

Anamnesis utilizes the complete suite of Cognee memory primitives:

| Cognee Primitive | How Anamnesis Uses It |
|---|---|
| **`remember()`** | Ingests commit diffs, bug fix reports (`root cause` + `fix` + `affected files`), and architecture docs (`ADRs`) into Cognee's graph/vector store linked to files and functions. |
| **`recall()`** | Automatically fired by the Git pre-commit hook (`.git/hooks/pre-commit`) or on-demand (`anamnesis ask "..."`) to surface past warnings connected to staged files. |
| **`memify()` / `reflect`** | Periodically clusters near-duplicate bug reports across files into generalized team rules (*e.g., "Null-check external API responses in the `services/` layer"*). |
| **`improve()`** | Runs graph enrichment, edge weight adaptation, and node optimization across the knowledge graph. |
| **`forget()`** | Decays obsolete memories when code is refactored (`anamnesis forget <id_or_file>`) so recall stops surfacing advice about dead code. |

---

## 4. Architecture

```
┌───────────────────────────────────────┐
│          Git Repository (Local)        │
│    commits / diffs / staged files     │
└───────────────────┬───────────────────┘
                    │ Git Hooks (.git/hooks/pre-commit)
                    ▼
┌───────────────────────────────────────┐
│         Anamnesis CLI (Python)        │
│   Typer Commands & Rich UI Formatter  │
│   init / remember-bug / ask / reflect │
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│          Cognee Memory Layer          │
│   remember / recall / memify / forget │
│   (GraphDB + Vector Storage Engine)   │
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│     LLM Provider / Cognee Cloud       │
│   (OpenAI, Anthropic, platform.cognee.ai)│
└───────────────────────────────────────┘
```

---

## 5. Quickstart & Installation

### Prerequisites
- Python 3.10 or higher
- Git

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/Anamnesis.git
   cd Anamnesis
   ```

2. **Create a virtual environment and install**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Initialize Anamnesis in your target repo**:
   ```bash
   anamnesis init
   ```
   *This ingests recent git commit history into Cognee memory and installs the Git pre-commit hook.*

---

## 6. CLI Command Reference

### `anamnesis init`
Initializes Anamnesis in the current repository, ingests commit history into Cognee memory, and installs `.git/hooks/pre-commit`.
```bash
anamnesis init [--repo <path>]
```

### `anamnesis remember-bug`
Logs a bug fix, its root cause, and fix details into codebase memory. Supports interactive prompts or auto-summarization from staged `git diff`.
```bash
# Manual interactive prompt
anamnesis remember-bug

# Auto-summarize staged diff
anamnesis remember-bug --auto

# With explicit flags
anamnesis remember-bug --file services/user_service.py --title "Unchecked API crash" --cause "Missing null check" --fix "Added guard clause"
```

### `anamnesis remember`
Ingests a general document, Architectural Decision Record (ADR), or PR note into the Cognee knowledge graph.
```bash
anamnesis remember "Use Service Layer for DB queries" --content "All direct DB queries must pass through services." --file services/base.py
```

### `anamnesis ask`
Query codebase memory graph in natural language for past bugs, warnings, and conventions.
```bash
anamnesis ask "Why do we validate external API responses in the service layer?"
```

### `anamnesis reflect`
Runs memory reflection to cluster related bug reports across files into consolidated team rules (`memify`).
```bash
anamnesis reflect
```

### `anamnesis rules`
Displays a clean Rich terminal table of all active consolidated team rules and their provenance links.
```bash
anamnesis rules
```

### `anamnesis improve`
Triggers post-ingestion graph relationship re-indexing, edge weight adaptation, and node optimization.
```bash
anamnesis improve
```

### `anamnesis forget`
Decays or removes stale memory items when code is deleted or refactored.
```bash
anamnesis forget mem_bug_8cec331b
anamnesis forget services/user_service.py
```

### `anamnesis status`
Renders a dashboard showing memory statistics, active rule counts, and Git hook installation status.
```bash
anamnesis status
```

### `anamnesis config`
Manage Cognee Cloud API keys and LLM provider configuration.
```bash
# Configure Cognee Cloud API key (from platform.cognee.ai)
anamnesis config set-cloud-key <your_cognee_api_key>

# Configure LLM API key
anamnesis config set-llm-key <your_openai_key>

# View active configuration dashboard
anamnesis config show
```

---

## 7. Cognee Cloud Platform Integration

Anamnesis works out of the box locally (with zero external database setup required) and seamlessly connects to **[Cognee Cloud](https://platform.cognee.ai)** for team-wide shared memory:

1. Claim your developer key on [platform.cognee.ai](https://platform.cognee.ai/sign-in).
2. Configure Anamnesis:
   ```bash
   anamnesis config set-cloud-key <your_platform_cognee_cloud_key>
   ```
3. Or set environment variables in `.env`:
   ```env
   COGNEE_API_KEY=your_platform_cognee_cloud_key
   COGNEE_API_URL=https://api.cognee.ai
   OPENAI_API_KEY=your_llm_key
   ```

---

## 8. Live Interactive Demo

Run the self-contained automated demo script to watch all 5 Cognee memory primitives in action:

```bash
python demo/run_demo.py
```

**What the demo demonstrates:**
1. **Setup**: Ingests baseline history and provisions Cognee memory graph.
2. **First bug (`remember`)**: Logs a null-check bug fix in `services/user_service.py`.
3. **Pre-commit hook (`recall`)**: Simulates editing `services/payment_service.py` with a similar flaw and fires an automatic warning panel.
4. **Consolidation (`memify/reflect`)**: Synthesizes individual bug reports into a consolidated team rule.
5. **Decay (`forget`)**: Surgically decays outdated memory after refactoring.
6. **Query (`ask`)**: Answers natural language architectural queries over the memory graph.

---

## 9. Running Tests

Run the full pytest suite:
```bash
pytest tests/
```

---

## 10. License

Licensed under the [MIT License](LICENSE).
