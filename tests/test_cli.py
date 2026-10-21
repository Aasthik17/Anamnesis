from pathlib import Path
import pytest
from typer.testing import CliRunner
from anamnesis.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def preserve_config():
    cfg = Path(".anamnesis/config.json")
    original = cfg.read_text(encoding="utf-8") if cfg.exists() else None
    yield
    if original is not None:
        cfg.write_text(original, encoding="utf-8")
    elif cfg.exists():
        cfg.unlink()

def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "Anamnesis version" in result.stdout

def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.stdout
    assert "remember-bug" in result.stdout
    assert "remember" in result.stdout
    assert "improve" in result.stdout
    assert "ask" in result.stdout
    assert "reflect" in result.stdout
    assert "rules" in result.stdout
    assert "forget" in result.stdout
    assert "status" in result.stdout

def test_cli_config():
    result_show = runner.invoke(app, ["config", "show"])
    assert result_show.exit_code == 0
    assert "Anamnesis Configuration Dashboard" in result_show.stdout

    result_set = runner.invoke(app, ["config", "set-cloud-key", "test-cognee-key-123"])
    assert result_set.exit_code == 0
    assert "Cognee Cloud API Key configured" in result_set.stdout

    result_backend = runner.invoke(app, ["config", "set-backend", "llama_cpp"])
    assert result_backend.exit_code == 0
    assert "LLM Backend configured to:" in result_backend.stdout
    assert "llama_cpp" in result_backend.stdout

    result_model = runner.invoke(app, ["config", "set-model", "/models/llama-3.1-8b-instruct-q4_k_m.gguf"])
    assert result_model.exit_code == 0
    assert "Model configured to:" in result_model.stdout

    result_quant = runner.invoke(app, ["config", "set-quantization", "Q4_K_M"])
    assert result_quant.exit_code == 0
    assert "Quantization level configured to:" in result_quant.stdout
    assert "Q4_K_M" in result_quant.stdout

    result_ctx = runner.invoke(app, ["config", "set-context", "2048"])
    assert result_ctx.exit_code == 0
    assert "Context window configured to:" in result_ctx.stdout
    assert "2048" in result_ctx.stdout

    result_mem = runner.invoke(app, ["config", "set-memory-budget", "4096"])
    assert result_mem.exit_code == 0
    assert "Memory budget configured to:" in result_mem.stdout
    assert "4096 MB" in result_mem.stdout
