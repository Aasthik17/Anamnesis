import os
import re
import platform
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union, List

logger = logging.getLogger(__name__)

# Standard recognized GGUF quantizations
KNOWN_QUANTIZATIONS = [
    "Q2_K",
    "Q3_K_S", "Q3_K_M", "Q3_K_L", "Q3_K",
    "Q4_0", "Q4_1", "Q4_K_S", "Q4_K_M", "Q4_K",
    "Q5_0", "Q5_1", "Q5_K_S", "Q5_K_M", "Q5_K",
    "Q6_K",
    "Q8_0",
    "F16", "BF16",
]


def is_llama_cpp_available() -> bool:
    """Check if the llama_cpp package is installed in the active environment."""
    try:
        import llama_cpp
        return True
    except ImportError:
        return False


def detect_quantization(model_path_or_name: Union[str, Path], fallback: str = "Q4_K_M") -> str:
    """
    Detect the quantization level (e.g. Q4_K_M, Q8_0) from a model filename or identifier.
    Returns the detected quantization string, or fallback if none is identified.
    """
    name = Path(model_path_or_name).name.upper()
    # Check for exact matches in tokens or parts separated by dots, dashes, underscores
    for quant in KNOWN_QUANTIZATIONS:
        pattern = rf"(?:^|[\-_\.]){re.escape(quant)}(?:[\-_\.]|$)"
        if re.search(pattern, name):
            return quant
    # Fallback to general substring check for common ones
    for quant in ["Q4_K_M", "Q5_K_M", "Q8_0", "Q2_K", "Q3_K", "Q6_K"]:
        if quant in name:
            return quant
    return fallback


def resolve_model_path(
    model_path: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
    repo_root: Optional[Path] = None,
    quantization: Optional[str] = None,
) -> Path:
    """
    Resolve the path to a quantized GGUF model file.

    Checks:
    1. Explicit `model_path` argument
    2. MODEL_PATH environment variable
    3. `model_path` in config
    4. LLM_MODEL env var or config if it points to a .gguf file
    5. Standard locations: ./models, .anamnesis/models, ~/.cache/anamnesis/models
    """
    from anamnesis.config import load_config, find_project_root

    if config is None:
        config = load_config(repo_root)

    root = repo_root or find_project_root()
    raw_path = model_path or os.getenv("MODEL_PATH") or config.get("model_path")

    # If raw_path is not given, check if llm_model looks like a file path
    if not raw_path:
        llm_model = os.getenv("LLM_MODEL") or config.get("llm_model")
        if llm_model and (llm_model.endswith(".gguf") or "/" in llm_model or "\\" in llm_model):
            raw_path = llm_model

    target_quant = quantization or os.getenv("MODEL_QUANTIZATION") or config.get("model_quantization") or "Q4_K_M"

    if raw_path:
        candidate = Path(raw_path).expanduser()
        if not candidate.is_absolute():
            candidate = (root / candidate).resolve()

        if candidate.is_file():
            return candidate

        # If it's an existing directory, search for GGUF files in it
        if candidate.is_dir():
            gguf_files = list(candidate.glob("*.gguf"))
            if gguf_files:
                # Prefer one matching target quantization
                for f in gguf_files:
                    if target_quant.lower() in f.name.lower():
                        return f
                return gguf_files[0]

    # Search in default project-relative and user-cache directories
    search_dirs = [
        root / "models",
        root / ".anamnesis" / "models",
        Path.home() / ".cache" / "anamnesis" / "models",
    ]

    for s_dir in search_dirs:
        if s_dir.exists() and s_dir.is_dir():
            gguf_files = list(s_dir.glob("*.gguf"))
            if gguf_files:
                for f in gguf_files:
                    if target_quant.lower() in f.name.lower():
                        return f
                return gguf_files[0]

    raise FileNotFoundError(
        f"GGUF model file not found at '{raw_path or 'unspecified path'}'.\n"
        "Please provide a valid quantized GGUF model path via:\n"
        "  • CLI: anamnesis config set-model /path/to/model.gguf\n"
        "  • Config: 'model_path' in .anamnesis/config.json\n"
        "  • Environment: MODEL_PATH=/path/to/model.gguf in .env"
    )


def calculate_memory_budget_params(
    memory_budget_mb: int = 4096,
    model_path: Optional[Path] = None,
    context_tokens: int = 4096,
    max_batch_size: int = 512,
    n_gpu_layers: int = 35,
) -> Dict[str, Any]:
    """
    Calculate and adapt runtime parameters (context window, batch size, GPU layers)
    based on the configured memory budget.

    Prevents out-of-memory crashes on constrained devices while maximizing
    performance within the allocated memory headroom.
    """
    budget = max(int(memory_budget_mb), 512)
    adjusted_ctx = int(context_tokens)
    adjusted_batch = int(max_batch_size)
    adjusted_layers = int(n_gpu_layers)

    model_size_mb = 0.0
    if model_path and Path(model_path).is_file():
        try:
            model_size_mb = Path(model_path).stat().st_size / (1024 * 1024)
        except OSError:
            pass

    # Constrained budget (< 2048 MB) or model taking up majority of budget
    if budget < 2048 or (model_size_mb > 0 and model_size_mb >= budget * 0.75):
        adjusted_ctx = min(adjusted_ctx, 1024 if budget < 1536 else 2048)
        adjusted_batch = min(adjusted_batch, 128)
        adjusted_layers = min(adjusted_layers, 10 if budget < 1536 else 20)
        logger.warning(
            f"Tight memory budget ({budget} MB). Adjusted parameters: "
            f"context={adjusted_ctx}, batch={adjusted_batch}, gpu_layers={adjusted_layers}"
        )
    # Moderate budget (2048MB - 4096MB)
    elif budget < 4096:
        adjusted_ctx = min(adjusted_ctx, 4096)
        adjusted_batch = min(adjusted_batch, 256)
        adjusted_layers = min(adjusted_layers, 28)
    # Standard budget (4096MB - 8192MB): use requested parameters up to defaults
    else:
        adjusted_ctx = max(adjusted_ctx, 2048)

    return {
        "n_ctx": adjusted_ctx,
        "n_batch": adjusted_batch,
        "n_gpu_layers": adjusted_layers,
        "memory_budget_mb": budget,
        "model_size_mb": round(model_size_mb, 2),
    }


def configure_apple_acceleration(
    coreml_enabled: bool = False,
    compute_units: str = "ALL",
) -> Dict[str, str]:
    """
    Configure environment variables for Apple Metal / CoreML runtime acceleration
    when running on macOS (Darwin).
    """
    flags: Dict[str, str] = {}
    if platform.system() == "Darwin" and coreml_enabled:
        flags["GGML_METAL"] = "1"
        flags["GGML_METAL_EMBEDDING"] = "1"
        flags["GGML_METAL_USE_BF16"] = "1"
        flags["COREML_ENABLED"] = "true"
        flags["COREML_COMPUTE_UNITS"] = compute_units

        for k, v in flags.items():
            if not os.getenv(k):
                os.environ[k] = v

    return flags


def get_llama_runtime(
    config: Optional[Dict[str, Any]] = None,
    repo_root: Optional[Path] = None,
    **runtime_kwargs,
) -> Any:
    """
    Factory that initializes and returns a `llama_cpp.Llama` instance.

    Validates dependencies, model path, quantisation, memory budgets,
    and platform-specific acceleration (Metal / CoreML on Apple Silicon).
    """
    if not is_llama_cpp_available():
        raise ImportError(
            "The 'llama-cpp-python' package is required for local quantized inference.\n"
            "Install it via:\n"
            "  pip install llama-cpp-python\n\n"
            "For Apple Silicon (macOS) with Metal & CoreML hardware acceleration:\n"
            '  CMAKE_ARGS="-DGGML_METAL=ON -DGGML_METAL_EMBEDDING=ON -DGGML_METAL_USE_BF16=ON" \\\n'
            "  pip install llama-cpp-python --upgrade --force-reinstall"
        )

    from anamnesis.config import load_config
    if config is None:
        config = load_config(repo_root)

    model_path = resolve_model_path(
        model_path=runtime_kwargs.get("model_path"),
        config=config,
        repo_root=repo_root,
        quantization=runtime_kwargs.get("model_quantization"),
    )

    # Resolve settings from kwargs, environment, or config
    budget_mb = int(runtime_kwargs.get("memory_budget_mb") or os.getenv("MEMORY_BUDGET_MB") or config.get("memory_budget_mb", 4096))
    context_tokens = int(runtime_kwargs.get("context_tokens") or os.getenv("CONTEXT_TOKENS") or config.get("context_tokens", 4096))
    max_batch_size = int(runtime_kwargs.get("max_batch_size") or os.getenv("MAX_BATCH_SIZE") or config.get("max_batch_size", 512))
    n_gpu_layers = int(runtime_kwargs.get("n_gpu_layers") or os.getenv("N_GPU_LAYERS") or config.get("n_gpu_layers", 35))
    threads = int(runtime_kwargs.get("threads") or os.getenv("THREADS") or config.get("threads", 8))

    use_mlock = runtime_kwargs.get("use_mlock")
    if use_mlock is None:
        env_mlock = os.getenv("USE_MLOCK")
        use_mlock = env_mlock.lower() in ("true", "1", "yes") if env_mlock else config.get("use_mlock", True)

    use_mmap = runtime_kwargs.get("use_mmap")
    if use_mmap is None:
        env_mmap = os.getenv("USE_MMAP")
        use_mmap = env_mmap.lower() in ("true", "1", "yes") if env_mmap else config.get("use_mmap", True)

    # CoreML / Metal acceleration
    coreml_enabled = runtime_kwargs.get("coreml_enabled")
    if coreml_enabled is None:
        env_coreml = os.getenv("COREML_ENABLED")
        coreml_enabled = env_coreml.lower() in ("true", "1", "yes") if env_coreml else config.get("coreml_enabled", False)

    compute_units = runtime_kwargs.get("coreml_compute_units") or os.getenv("COREML_COMPUTE_UNITS") or config.get("coreml_compute_units", "ALL")

    configure_apple_acceleration(coreml_enabled=bool(coreml_enabled), compute_units=compute_units)

    budget_params = calculate_memory_budget_params(
        memory_budget_mb=budget_mb,
        model_path=model_path,
        context_tokens=context_tokens,
        max_batch_size=max_batch_size,
        n_gpu_layers=n_gpu_layers,
    )

    import llama_cpp

    init_args = {
        "model_path": str(model_path),
        "n_ctx": budget_params["n_ctx"],
        "n_batch": budget_params["n_batch"],
        "n_gpu_layers": budget_params["n_gpu_layers"],
        "n_threads": threads,
        "use_mlock": bool(use_mlock),
        "use_mmap": bool(use_mmap),
        "verbose": False,
    }

    # Pass through any extra caller kwargs
    for k, v in runtime_kwargs.items():
        if k not in init_args and k not in (
            "memory_budget_mb", "context_tokens", "max_batch_size",
            "coreml_enabled", "coreml_compute_units", "model_quantization"
        ):
            init_args[k] = v

    return llama_cpp.Llama(**init_args)


def generate_completion(
    messages: Union[str, List[Dict[str, str]]],
    config: Optional[Dict[str, Any]] = None,
    max_tokens: int = 512,
    temperature: float = 0.2,
    response_format: Optional[Dict[str, str]] = None,
    repo_root: Optional[Path] = None,
) -> str:
    """
    Generate completion or chat response using the local llama.cpp runtime.
    """
    llm = get_llama_runtime(config=config, repo_root=repo_root)

    if isinstance(messages, str):
        msg_list = [
            {"role": "user", "content": messages}
        ]
    else:
        msg_list = messages

    kwargs: Dict[str, Any] = {
        "messages": msg_list,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if response_format:
        kwargs["response_format"] = response_format

    response = llm.create_chat_completion(**kwargs)
    choice = response["choices"][0]
    return choice["message"]["content"]
