import os
import sys
from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from anamnesis import __version__
from anamnesis.config import load_config, save_config, find_project_root
from anamnesis.memory.client import MemoryClient
from anamnesis.memory.schemas import BugFixMemory, MemoryType
from anamnesis.memory.consolidator import MemoryConsolidator
from anamnesis.git.inspector import GitInspector
from anamnesis.git.hooks import HookManager
from anamnesis.ui.formatter import (
    render_banner,
    render_memory_warning,
    render_recall_response,
    render_rules_table,
    render_status_dashboard,
)
from anamnesis.utils.llm_helper import summarize_diff_with_llm

app = typer.Typer(
    name="anamnesis",
    help="A CLI companion that gives your codebase a long-term memory using Cognee AI",
    add_completion=False,
)
hook_app = typer.Typer(help="Git hook execution subcommands")
config_app = typer.Typer(help="Anamnesis & Cognee Cloud configuration subcommands")
app.add_typer(hook_app, name="hook")
app.add_typer(config_app, name="config")

console = Console()

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit"),
):
    if version:
        console.print(f"[bold cyan]Anamnesis[/bold cyan] version [bold white]{__version__}[/bold white]")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        render_banner()
        console.print("[yellow]Use --help to see available commands.[/yellow]\n")

@app.command("init")
def init_cmd(
    repo_path: Optional[Path] = typer.Option(None, "--repo", "-r", help="Path to git repository root"),
):
    """
    [COGNEE PRIMITIVE: remember]
    Initialize Anamnesis in the repo: ingest commit history and setup git hooks.
    """
    render_banner()
    root = (repo_path or find_project_root()).resolve()
    console.print(f"[bold cyan]Initializing Anamnesis in:[/bold cyan] [white]{root}[/white]")

    client = MemoryClient(root)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Ingesting git commit history into Cognee...", total=None)
        commits = GitInspector.get_commit_history(root, max_commits=10)
        for commit in commits:
            client.remember_commit(commit)

    console.print(f"  [green]✓ Ingested {len(commits)} historical git commits into memory.[/green]")

    # Install Git Pre-Commit Hook
    if HookManager.install_pre_commit_hook(root):
        console.print("  [green]✓ Installed Git pre-commit recall hook (.git/hooks/pre-commit).[/green]")
    else:
        console.print("  [yellow]! Git directory not found; skipping hook installation.[/yellow]")

    config = load_config(root)
    config["initialized"] = True
    save_config(config, root)

    console.print("\n[bold green]🎉 Anamnesis is ready![/bold green] Your codebase now has a long-term memory graph.\n")

@app.command("remember-bug")
def remember_bug_cmd(
    file_path: Optional[str] = typer.Option(None, "--file", "-f", help="Affected file path"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Short bug summary"),
    root_cause: Optional[str] = typer.Option(None, "--cause", "-c", help="Root cause of the bug"),
    fix: Optional[str] = typer.Option(None, "--fix", "-x", help="Fix description"),
    auto: bool = typer.Option(False, "--auto", "-a", help="Auto-summarize from staged git diff"),
):
    """
    [COGNEE PRIMITIVE: remember]
    Manually log a bug fix and its root cause into codebase memory.
    """
    root = find_project_root()
    client = MemoryClient(root)

    if auto:
        staged_diff = GitInspector.get_staged_diff(root)
        if not staged_diff:
            console.print("[yellow]No staged git diff found. Falling back to manual input.[/yellow]")
        else:
            summary_data = summarize_diff_with_llm(staged_diff)
            title = title or summary_data["title"]
            root_cause = root_cause or summary_data["root_cause"]
            fix = fix or summary_data["fix_description"]
            staged_files = GitInspector.get_staged_files(root)
            if staged_files:
                file_path = file_path or staged_files[0]

    # Prompt interactively if parameters missing
    if not file_path:
        file_path = typer.prompt("Path to affected file (e.g. services/user_service.py)")
    if not title:
        title = typer.prompt("Bug title/summary")
    if not root_cause:
        root_cause = typer.prompt("Root cause (why did it happen?)")
    if not fix:
        fix = typer.prompt("Fix applied (how was it solved?)")

    bug_mem = BugFixMemory(
        file_path=file_path,
        title=title,
        root_cause=root_cause,
        fix_description=fix,
        tags=["bug", Path(file_path).stem]
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Pushing bug memory into Cognee graph...", total=None)
        rec = client.remember_bug(bug_mem)

    console.print(f"\n[bold green]✓ Memory logged successfully![/bold green] (ID: [cyan]{rec.id}[/cyan])")
    console.print(f"  File: [cyan]{file_path}[/cyan]")
    console.print(f"  Root Cause: {root_cause}")

@app.command("remember")
def remember_cmd(
    title: str = typer.Argument(..., help="Title or header for the memory entry"),
    content: Optional[str] = typer.Option(None, "--content", "-c", help="Text content or body"),
    file_path: Optional[str] = typer.Option(None, "--file", "-f", help="Optional file path context"),
):
    """
    [COGNEE PRIMITIVE: remember]
    Ingest a general document, ADR, PR description, or note into Cognee memory graph.
    """
    root = find_project_root()
    client = MemoryClient(root)

    if not content:
        content = typer.prompt("Enter document content / notes")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Ingesting document into Cognee knowledge graph...", total=None)
        rec = client.remember_doc(title=title, content=content, file_path=file_path)

    console.print(f"\n[bold green]✓ Document ingested into Cognee memory![/bold green] (ID: [cyan]{rec.id}[/cyan])")

@app.command("improve")
def improve_cmd():
    """
    [COGNEE PRIMITIVE: improve / memify]
    Run post-ingestion graph enrichment and refine codebase memory.
    """
    root = find_project_root()
    client = MemoryClient(root)
    
    console.print("\n[bold cyan]⚡ Running Cognee Graph Enrichment & Memory Improvement...[/bold cyan]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Re-indexing relationships and optimizing memory weights...", total=None)
        client.improve()

    console.print("[bold green]✓ Memory graph improved and optimized successfully![/bold green]\n")

@app.command("ask")
def ask_cmd(
    query: str = typer.Argument(..., help="Natural language question to ask codebase memory"),
    file_context: Optional[str] = typer.Option(None, "--file", "-f", help="Optional file context filter"),
):
    """
    [COGNEE PRIMITIVE: recall]
    Query codebase memory graph for past bugs, warnings, and conventions.
    """
    root = find_project_root()
    client = MemoryClient(root)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Traversing Cognee memory graph...", total=None)
        records = client.recall(query=query, file_context=file_context, top_k=5)

    render_recall_response(query, records)

@app.command("reflect")
def reflect_cmd():
    """
    [COGNEE PRIMITIVE: memify / reflect]
    Consolidate near-duplicate bug reports into higher-level team rules.
    """
    root = find_project_root()
    client = MemoryClient(root)
    consolidator = MemoryConsolidator(client)

    console.print("\n[bold cyan]🧠 Running Memory Reflection & Consolidation...[/bold cyan]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Clustering memory patterns via Cognee memify...", total=None)
        new_rules = consolidator.reflect()

    if new_rules:
        console.print(f"\n[bold green]🎉 Synthesized {len(new_rules)} new consolidated rule(s):[/bold green]\n")
        for r in new_rules:
            console.print(f"  • [bold yellow]{r.rule_title}[/bold yellow] ([dim]Domain: {r.domain}[/dim])")
            console.print(f"    [dim]{r.description}[/dim]\n")
    else:
        console.print("\n[dim]No new clusters found to consolidate. Existing rules are up to date.[/dim]\n")

@app.command("rules")
def rules_cmd():
    """
    List all active consolidated team rules and their provenance.
    """
    root = find_project_root()
    client = MemoryClient(root)
    rules = client.get_rules()
    render_rules_table(rules)

@app.command("forget")
def forget_cmd(
    target: str = typer.Argument(..., help="Memory ID or file path to forget/decay"),
):
    """
    [COGNEE PRIMITIVE: forget]
    Remove or decay stale memory when code is deleted or refactored.
    """
    root = find_project_root()
    client = MemoryClient(root)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Decaying target memory in Cognee...", total=None)
        removed = client.forget(target)

    if removed:
        console.print(f"\n[bold green]✓ Successfully forgot {len(removed)} memory item(s):[/bold green] [cyan]{', '.join(removed)}[/cyan]")
    else:
        console.print(f"\n[yellow]No active memories found matching '[bold white]{target}[/bold white]'.[/yellow]")

@app.command("status")
def status_cmd():
    """
    Display memory graph statistics and system health dashboard.
    """
    root = find_project_root()
    client = MemoryClient(root)
    memories = client.list_memories()
    config = load_config(root)

    stats = {
        "total_memories": len(memories),
        "bug_fixes": len([m for m in memories if m.memory_type == MemoryType.BUG_FIX]),
        "rules": len([m for m in memories if m.memory_type == MemoryType.RULE]),
        "commits": len([m for m in memories if m.memory_type == MemoryType.COMMIT]),
        "hooks_installed": config.get("hooks_installed", False),
        "backend": "Local SQLite + Cognee Vector Index"
    }

    render_status_dashboard(stats)

@config_app.command("set-cloud-key")
def set_cloud_key_cmd(
    key: str = typer.Argument(..., help="Cognee Cloud API key from platform.cognee.ai"),
    url: str = typer.Option("https://api.cognee.ai", "--url", "-u", help="Cognee Cloud API endpoint URL"),
):
    """
    Configure your Cognee Cloud API Key for extended memory storage.
    """
    root = find_project_root()
    config = load_config(root)
    config["cognee_api_key"] = key.strip()
    config["cognee_api_url"] = url.strip()
    config["use_cloud"] = True
    save_config(config, root)

    # Also update local .env file
    env_path = root / ".env"
    lines = []
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = [l for l in f.readlines() if not l.startswith("COGNEE_API_KEY") and not l.startswith("COGNEE_API_URL")]
    lines.append(f"COGNEE_API_KEY={key.strip()}\n")
    lines.append(f"COGNEE_API_URL={url.strip()}\n")
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    console.print(f"\n[bold green]✓ Cognee Cloud API Key configured successfully![/bold green]")
    console.print(f"  Endpoint: [cyan]{url}[/cyan]\n")

@config_app.command("set-llm-key")
def set_llm_key_cmd(
    key: str = typer.Argument(..., help="LLM API Key (OpenAI / Anthropic / LiteLLM)"),
):
    """
    Configure LLM API Key for auto-summarizing commit diffs and synthesizing recall answers.
    """
    root = find_project_root()
    config = load_config(root)
    config["llm_api_key"] = key.strip()
    save_config(config, root)

    env_path = root / ".env"
    lines = []
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = [l for l in f.readlines() if not l.startswith("OPENAI_API_KEY")]
    lines.append(f"OPENAI_API_KEY={key.strip()}\n")
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    console.print(f"\n[bold green]✓ LLM API Key configured successfully![/bold green]\n")

@config_app.command("show")
def config_show_cmd():
    """
    Display active Anamnesis configuration and Cognee Cloud connection status.
    """
    root = find_project_root()
    config = load_config(root)

    cognee_key = os.getenv("COGNEE_API_KEY") or config.get("cognee_api_key")
    llm_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or config.get("llm_api_key")

    def mask_key(k: Optional[str]) -> str:
        if not k:
            return "[yellow]Not set[/yellow]"
        return f"[green]{k[:4]}...{k[-4:]}[/green]" if len(k) > 8 else "[green]Configured[/green]"

    console.print("\n[bold cyan]⚙️  Anamnesis Configuration Dashboard[/bold cyan]\n")
    console.print(f"  Project Root: [white]{root}[/white]")
    console.print(f"  Cognee Cloud API Key: {mask_key(cognee_key)}")
    console.print(f"  Cognee Cloud Endpoint: [cyan]{config.get('cognee_api_url', 'https://api.cognee.ai')}[/cyan]")
    console.print(f"  LLM Provider Key: {mask_key(llm_key)}")
    console.print(f"  Pre-Commit Hook: {'[green]Installed[/green]' if config.get('hooks_installed') else '[yellow]Not Installed[/yellow]'}\n")

@hook_app.command("run")
def hook_run_cmd(
    stage: str = typer.Option("pre-commit", "--stage", help="Hook stage name"),
):
    """Internal handler executed by git pre-commit hook."""
    root = find_project_root()
    result = HookManager.execute_pre_commit_check(root)
    warnings = result.get("warnings", [])

    if warnings:
        console.print("\n[bold yellow]════════════════════════════════════════════════════════════════[/bold yellow]")
        console.print("[bold yellow]  ⚠️  ANAMNESIS PRE-COMMIT MEMORY WARNINGS[/bold yellow]")
        console.print("[bold yellow]════════════════════════════════════════════════════════════════[/bold yellow]\n")
        for w in warnings:
            console.print(render_memory_warning(w))
        console.print("[dim]Review previous bug history above before completing commit.[/dim]\n")

if __name__ == "__main__":
    app()
