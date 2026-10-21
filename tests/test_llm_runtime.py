import os
import platform
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from anamnesis.config import DEFAULT_CONFIG, configure_llm_env, load_config
from anamnesis.llm_runtime import (
    detect_quantization,
    resolve_model_path,
    calculate_memory_budget_params,
    configure_apple_acceleration,
    get_llama_runtime,
    is_llama_cpp_available,
)


@pytest.fixture(autouse=True)
def clean_environment():
    """Isolate environment variables between tests."""
    old_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(old_env)


def test_default_config_fields():
    """Verify DEFAULT_CONFIG includes all quantisation, llama.cpp, and memory budget fields."""
    assert DEFAULT_CONFIG["llm_backend"] == "llama_cpp"
    assert DEFAULT_CONFIG["model_path"] is None
    assert DEFAULT_CONFIG["model_quantization"] == "Q4_K_M"
    assert DEFAULT_CONFIG["context_tokens"] == 4096
    assert DEFAULT_CONFIG["max_batch_size"] == 512
    assert DEFAULT_CONFIG["n_gpu_layers"] == 35
    assert DEFAULT_CONFIG["threads"] == 8
    assert DEFAULT_CONFIG["use_mlock"] is True
    assert DEFAULT_CONFIG["use_mmap"] is True
    assert DEFAULT_CONFIG["memory_budget_mb"] == 4096
    assert DEFAULT_CONFIG["coreml_enabled"] is False
    assert DEFAULT_CONFIG["coreml_compute_units"] == "ALL"


def test_configure_llm_env_llama_cpp(monkeypatch):
    """Test configure_llm_env with llama_cpp provider."""
    # Clear any conflicting env vars
    for k in [
        "LLM_PROVIDER", "LLM_BACKEND", "LLM_MODEL", "MODEL_PATH",
        "MODEL_QUANTIZATION", "CONTEXT_TOKENS", "MAX_BATCH_SIZE",
        "N_GPU_LAYERS", "THREADS", "MEMORY_BUDGET_MB", "COREML_ENABLED",
        "GGML_METAL", "GGML_METAL_EMBEDDING", "GGML_METAL_USE_BF16",
    ]:
        monkeypatch.delenv(k, raising=False)

    test_config = {
        "llm_provider": "llama_cpp",
        "model_path": "/test/models/llama-3.1-8b-instruct-q4_k_m.gguf",
        "model_quantization": "Q4_K_M",
        "context_tokens": 2048,
        "max_batch_size": 256,
        "n_gpu_layers": 28,
        "threads": 4,
        "memory_budget_mb": 4096,
        "coreml_enabled": True,
        "coreml_compute_units": "ALL",
    }

    resolved = configure_llm_env(test_config)
    assert resolved == "llama_cpp"
    assert os.environ.get("LLM_PROVIDER") == "llama_cpp"
    assert os.environ.get("MODEL_PATH") == "/test/models/llama-3.1-8b-instruct-q4_k_m.gguf"
    assert os.environ.get("MODEL_QUANTIZATION") == "Q4_K_M"
    assert os.environ.get("CONTEXT_TOKENS") == "2048"
    assert os.environ.get("MAX_BATCH_SIZE") == "256"
    assert os.environ.get("N_GPU_LAYERS") == "28"
    assert os.environ.get("THREADS") == "4"
    assert os.environ.get("MEMORY_BUDGET_MB") == "4096"

    if platform.system() == "Darwin":
        assert os.environ.get("GGML_METAL") == "1"
        assert os.environ.get("GGML_METAL_EMBEDDING") == "1"
        assert os.environ.get("GGML_METAL_USE_BF16") == "1"
        assert os.environ.get("COREML_ENABLED") == "true"


def test_env_precedence_over_config(monkeypatch):
    """Ensure existing environment variables take precedence over config."""
    monkeypatch.setenv("LLM_PROVIDER", "llama_cpp")
    monkeypatch.setenv("MODEL_QUANTIZATION", "Q8_0")
    monkeypatch.setenv("MEMORY_BUDGET_MB", "8192")

    test_config = {
        "llm_provider": "ollama",
        "model_quantization": "Q4_K_M",
        "memory_budget_mb": 2048,
    }

    resolved = configure_llm_env(test_config)
    assert resolved == "llama_cpp"
    assert os.environ.get("MODEL_QUANTIZATION") == "Q8_0"
    assert os.environ.get("MEMORY_BUDGET_MB") == "8192"


def test_preserve_ollama_and_openai(monkeypatch):
    """Ensure existing Ollama and OpenAI provider flows remain fully functional."""
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # Ollama
    ollama_config = {
        "llm_provider": "ollama",
        "llm_model": "llama3.1:8b",
        "embedding_model": "nomic-embed-text",
    }
    assert configure_llm_env(ollama_config) == "ollama"
    assert os.environ.get("EMBEDDING_PROVIDER") == "ollama"

    # OpenAI
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    openai_config = {
        "llm_provider": "openai",
        "llm_api_key": "sk-test-key",
        "llm_model": "gpt-4o-mini",
    }
    assert configure_llm_env(openai_config) == "openai"


def test_detect_quantization():
    """Verify quantization string extraction from filenames."""
    assert detect_quantization("llama-3.1-8b-instruct-q4_k_m.gguf") == "Q4_K_M"
    assert detect_quantization("/path/to/mistral-7b-v0.1.Q8_0.gguf") == "Q8_0"
    assert detect_quantization("deepseek-coder-q5_k_m.gguf") == "Q5_K_M"
    assert detect_quantization("model.q2_k.gguf") == "Q2_K"
    assert detect_quantization("unknown_model.gguf", fallback="Q4_K_M") == "Q4_K_M"


def test_calculate_memory_budget_params(tmp_path):
    """Test dynamic parameter scaling under different memory budgets."""
    dummy_model = tmp_path / "model.gguf"
    # Create a 2000 MB dummy file
    with open(dummy_model, "wb") as f:
        f.seek(2000 * 1024 * 1024 - 1)
        f.write(b"\0")

    # Tight budget: 1500 MB budget for 2000 MB model
    tight_params = calculate_memory_budget_params(
        memory_budget_mb=1500,
        model_path=dummy_model,
        context_tokens=4096,
        max_batch_size=512,
        n_gpu_layers=35,
    )
    assert tight_params["n_ctx"] <= 2048
    assert tight_params["n_batch"] <= 128
    assert tight_params["n_gpu_layers"] <= 20

    # Ample budget: 8192 MB
    ample_params = calculate_memory_budget_params(
        memory_budget_mb=8192,
        model_path=dummy_model,
        context_tokens=4096,
        max_batch_size=512,
        n_gpu_layers=35,
    )
    assert ample_params["n_ctx"] == 4096
    assert ample_params["n_batch"] == 512
    assert ample_params["n_gpu_layers"] == 35


def test_resolve_model_path(tmp_path):
    """Test resolving existing and missing GGUF model files."""
    model_file = tmp_path / "llama-q4_k_m.gguf"
    model_file.write_text("dummy gguf header")

    resolved = resolve_model_path(model_path=str(model_file))
    assert resolved == model_file

    with pytest.raises(FileNotFoundError) as exc_info:
        resolve_model_path(model_path="/non/existent/model.gguf", repo_root=tmp_path)
    assert "GGUF model file not found" in str(exc_info.value)


def test_get_llama_runtime_missing_package():
    """Verify get_llama_runtime raises clear ImportError when llama_cpp is absent."""
    with patch("anamnesis.llm_runtime.is_llama_cpp_available", return_value=False):
        with pytest.raises(ImportError) as exc_info:
            get_llama_runtime()
        assert "llama-cpp-python" in str(exc_info.value)
        assert "CMAKE_ARGS" in str(exc_info.value)


def test_get_llama_runtime_instantiation(tmp_path, monkeypatch):
    """Verify get_llama_runtime passes correct parameters to llama_cpp.Llama."""
    monkeypatch.delenv("MODEL_PATH", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    model_file = tmp_path / "model-q4_k_m.gguf"
    model_file.write_text("dummy")

    mock_llama_cls = MagicMock()
    mock_module = MagicMock()
    mock_module.Llama = mock_llama_cls

    with patch("anamnesis.llm_runtime.is_llama_cpp_available", return_value=True):
        with patch.dict("sys.modules", {"llama_cpp": mock_module}):
            get_llama_runtime(
                config={
                    "model_path": str(model_file),
                    "context_tokens": 2048,
                    "max_batch_size": 256,
                    "n_gpu_layers": 16,
                    "threads": 4,
                    "memory_budget_mb": 4096,
                }
            )
            mock_llama_cls.assert_called_once()
            call_kwargs = mock_llama_cls.call_args[1]
            assert call_kwargs["model_path"] == str(model_file)
            assert call_kwargs["n_ctx"] == 2048
            assert call_kwargs["n_batch"] == 256
            assert call_kwargs["n_gpu_layers"] == 16
            assert call_kwargs["n_threads"] == 4


def test_summarize_diff_with_llama_cpp(monkeypatch):
    """Verify summarize_diff_with_llm invokes generate_completion when llama_cpp is active."""
    monkeypatch.setenv("LLM_PROVIDER", "llama_cpp")
    from anamnesis.utils.llm_helper import summarize_diff_with_llm

    fake_diff = "--- a/test.py\n+++ b/test.py\n@@ -1,2 +1,3 @@\n+if user is not None:\n     user.save()"
    fake_json = '{"title": "Null check patch", "root_cause": "Missing null guard", "fix_description": "Added user check"}'

    with patch("anamnesis.llm_runtime.generate_completion", return_value=fake_json) as mock_gen:
        summary = summarize_diff_with_llm(fake_diff)
        mock_gen.assert_called_once()
        assert summary["title"] == "Null check patch"
        assert summary["root_cause"] == "Missing null guard"
        assert summary["fix_description"] == "Added user check"

    # Test fallback if llama_cpp fails
    with patch("anamnesis.llm_runtime.generate_completion", side_effect=Exception("Model unavailable")):
        summary_fallback = summarize_diff_with_llm(fake_diff)
        assert "null" in summary_fallback["title"].lower() or "fix" in summary_fallback["title"].lower()

