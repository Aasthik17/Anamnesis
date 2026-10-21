import os
import json
import platform
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DEFAULT_CONFIG = {
    "version": "0.1.0",
    "storage_dir": ".anamnesis",
    "hooks_installed": False,
    "max_context_diffs": 5,
    "reflection_threshold": 3,
    "cognee_api_key": None,
    "cognee_api_url": "https://api.cognee.ai",
    # LLM / embedding backend. "ollama" runs everything locally and free (no API
    # key required). "openai" uses a paid OpenAI key. "llama_cpp" uses local
    # quantized GGUF models. See configure_llm_env().
    "llm_provider": "ollama",
    "llm_api_key": None,
    "llm_model": "llama3.1:8b",
    "embedding_model": "nomic-embed-text",
    "embedding_dimensions": 768,
    "ollama_base_url": "http://localhost:11434/v1",
    # Advanced graph extraction (typed CodeKnowledgeGraph schema + temporal event
    # tracking) needs a strong LLM that reliably emits strict structured JSON.
    # Small local models (e.g. llama3.2:3b) can't, so these default OFF and we use
    # Cognee's robust built-in extraction. Turn ON only with a strong model
    # (OpenAI, or a large local model like llama3.1:70b).
    "use_custom_graph_schema": False,
    "use_temporal_cognify": False,
    "use_cloud": False,

    # New llama.cpp / quantized inference settings
    "llm_backend": "llama_cpp",
    "model_path": None,
    "model_quantization": "Q4_K_M",
    "context_tokens": 4096,
    "max_batch_size": 512,
    "n_gpu_layers": 35,
    "threads": 8,
    "use_mlock": True,
    "use_mmap": True,
    "memory_budget_mb": 4096,
    "coreml_enabled": False,
    "coreml_compute_units": "ALL",
}

def find_project_root(start_path: Optional[Path] = None) -> Path:
    """Find the root directory of the repository (where .git or .anamnesis resides)."""
    current = (start_path or Path.cwd()).resolve()
    for dir_path in [current] + list(current.parents):
        if (dir_path / ".git").exists() or (dir_path / ".anamnesis").exists():
            return dir_path
    return current

def get_anamnesis_dir(repo_root: Optional[Path] = None) -> Path:
    root = repo_root or find_project_root()
    anamnesis_dir = root / ".anamnesis"
    anamnesis_dir.mkdir(parents=True, exist_ok=True)
    return anamnesis_dir

def get_config_path(repo_root: Optional[Path] = None) -> Path:
    return get_anamnesis_dir(repo_root) / "config.json"

def load_config(repo_root: Optional[Path] = None) -> Dict[str, Any]:
    config_path = get_config_path(repo_root)
    if not config_path.exists():
        return DEFAULT_CONFIG.copy()
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)
            return merged
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any], repo_root: Optional[Path] = None) -> None:
    config_path = get_config_path(repo_root)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def configure_llm_env(config: Optional[Dict[str, Any]] = None) -> str:
    """
    Export the environment variables that Cognee/LiteLLM, llama.cpp runtime,
    and the raw OpenAI SDK need, based on the configured LLM provider.

    Returns the resolved provider name ("ollama", "openai", or "llama_cpp").

    Existing environment variables always win, so anything already set in .env or
    the shell overrides these defaults — this only fills in the blanks.

    - "ollama"    → fully local & free. Points chat + embeddings at a local Ollama
                    server (default http://localhost:11434). No API key required.
    - "llama_cpp" → local quantized inference with GGUF models. Supports Metal / CoreML
                    acceleration on Apple Silicon, memory budgeting, and configurable
                    quantization (e.g. Q4_K_M).
    - "openai"    → uses OPENAI_API_KEY (paid).
    """
    if config is None:
        config = load_config()

    def setdefault(key: str, value: Optional[str]) -> None:
        if value is not None and not os.getenv(key):
            os.environ[key] = str(value)

    provider = (os.getenv("LLM_PROVIDER") or config.get("llm_provider") or "openai").lower()

    if provider in ("llama_cpp", "llamacpp"):
        provider = "llama_cpp"
        model_path = os.getenv("MODEL_PATH") or config.get("model_path")
        quantization = os.getenv("MODEL_QUANTIZATION") or config.get("model_quantization") or "Q4_K_M"
        context_tokens = os.getenv("CONTEXT_TOKENS") or str(config.get("context_tokens", 4096))
        max_batch_size = os.getenv("MAX_BATCH_SIZE") or str(config.get("max_batch_size", 512))
        n_gpu_layers = os.getenv("N_GPU_LAYERS") or str(config.get("n_gpu_layers", 35))
        threads = os.getenv("THREADS") or str(config.get("threads", 8))
        memory_budget_mb = os.getenv("MEMORY_BUDGET_MB") or str(config.get("memory_budget_mb", 4096))
        use_mlock = os.getenv("USE_MLOCK") or str(config.get("use_mlock", True)).lower()
        use_mmap = os.getenv("USE_MMAP") or str(config.get("use_mmap", True)).lower()

        # CoreML / Metal settings
        coreml_env = os.getenv("COREML_ENABLED")
        if coreml_env is not None:
            coreml_enabled = coreml_env.lower() in ("true", "1", "yes", "on")
        else:
            coreml_enabled = bool(config.get("coreml_enabled", False))

        coreml_compute_units = os.getenv("COREML_COMPUTE_UNITS") or config.get("coreml_compute_units", "ALL")

        chat_model = os.getenv("LLM_MODEL") or config.get("llm_model")
        if not chat_model and model_path:
            chat_model = Path(model_path).name
        if not chat_model:
            chat_model = f"llama-3.1-8b-instruct-{quantization.lower()}.gguf"

        setdefault("LLM_PROVIDER", "llama_cpp")
        setdefault("LLM_BACKEND", "llama_cpp")
        setdefault("LLM_MODEL", chat_model)
        setdefault("ANAMNESIS_LLM_MODEL", chat_model)
        if model_path:
            setdefault("MODEL_PATH", str(model_path))
        setdefault("MODEL_QUANTIZATION", quantization)
        setdefault("CONTEXT_TOKENS", str(context_tokens))
        setdefault("MAX_BATCH_SIZE", str(max_batch_size))
        setdefault("N_GPU_LAYERS", str(n_gpu_layers))
        setdefault("THREADS", str(threads))
        setdefault("MEMORY_BUDGET_MB", str(memory_budget_mb))
        setdefault("USE_MLOCK", str(use_mlock))
        setdefault("USE_MMAP", str(use_mmap))
        setdefault("COREML_COMPUTE_UNITS", coreml_compute_units)

        if platform.system() == "Darwin" and coreml_enabled:
            setdefault("COREML_ENABLED", "true")
            setdefault("GGML_METAL", "1")
            setdefault("GGML_METAL_EMBEDDING", "1")
            setdefault("GGML_METAL_USE_BF16", "1")
        else:
            setdefault("COREML_ENABLED", str(coreml_enabled).lower())

        # Optional OpenAI compatibility if local llama.cpp server is configured
        llama_endpoint = os.getenv("LLM_ENDPOINT") or os.getenv("OPENAI_BASE_URL")
        if llama_endpoint:
            setdefault("OPENAI_BASE_URL", llama_endpoint)
            setdefault("OPENAI_API_KEY", "llama_cpp")
            setdefault("LLM_API_KEY", "llama_cpp")

        return provider

    if provider == "ollama":
        base = os.getenv("LLM_ENDPOINT") or config.get("ollama_base_url") or "http://localhost:11434/v1"
        host = base.replace("/v1", "")
        chat_model = config.get("llm_model") or "llama3.1:8b"
        embed_model = config.get("embedding_model") or "nomic-embed-text"
        embed_dims = config.get("embedding_dimensions", 768)
        # Cognee's OllamaEmbeddingEngine posts {"input": ...} and reads "embeddings"
        # — that is Ollama's newer /api/embed batch endpoint, NOT /api/embeddings.
        embed_endpoint = host + "/api/embed"
        # The Ollama embedder loads a HuggingFace tokenizer (via `transformers`) for
        # token counting. It has no default, so we must name one that matches the
        # embedding model or Cognee queries huggingface.co/None and 401s.
        hf_tokenizer = config.get("embedding_tokenizer") or "nomic-ai/nomic-embed-text-v1.5"

        # Cognee / LiteLLM configuration
        setdefault("LLM_PROVIDER", "ollama")
        setdefault("LLM_MODEL", chat_model)
        setdefault("LLM_ENDPOINT", base)
        setdefault("LLM_API_KEY", "ollama")  # Ollama ignores the value but LiteLLM needs one
        setdefault("EMBEDDING_PROVIDER", "ollama")
        setdefault("EMBEDDING_MODEL", embed_model)
        setdefault("EMBEDDING_ENDPOINT", embed_endpoint)
        setdefault("EMBEDDING_API_KEY", "ollama")
        setdefault("EMBEDDING_DIMENSIONS", embed_dims)
        setdefault("EMBEDDING_MAX_COMPLETION_TOKENS", 8192)
        setdefault("HUGGINGFACE_TOKENIZER", hf_tokenizer)

        # Raw `openai` SDK calls (llm_helper, consolidator) route through Ollama's
        # OpenAI-compatible endpoint.
        setdefault("OPENAI_API_KEY", "ollama")
        setdefault("OPENAI_BASE_URL", base)
        setdefault("ANAMNESIS_LLM_MODEL", chat_model)
        return provider

    # Default: OpenAI (or any OPENAI_API_KEY-compatible provider)
    llm_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or config.get("llm_api_key")
    if llm_key:
        setdefault("OPENAI_API_KEY", llm_key)
    setdefault("ANAMNESIS_LLM_MODEL", config.get("llm_model") or "gpt-4o-mini")
    return provider
