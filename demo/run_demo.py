import os
import sys
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

# Ensure root package is importable
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from anamnesis.memory.client import MemoryClient
from anamnesis.memory.schemas import BugFixMemory, MemoryType
from anamnesis.memory.consolidator import MemoryConsolidator
from anamnesis.git.hooks import HookManager
from anamnesis.ui.formatter import (
    render_banner, render_memory_warning, render_recall_response,
    render_rules_table, render_status_dashboard
)

console = Console()

def pause(msg: str = "Press Enter to continue to next demo step..."):
    console.print(f"\n[dim yellow]▶ {msg}[/dim yellow]")

def run_full_demo():
    sample_dir = root_dir / "demo" / "sample_project"
    
    render_banner()
    console.print(Panel(
        "[bold cyan]ANAMNESIS LIVE DEMO WORKFLOW[/bold cyan]\n\n"
        "Demonstrating the 4 core Cognee memory primitives:\n"
        " 1. [bold white]remember[/bold white]: Ingestion of historical git context & bug fixes\n"
        " 2. [bold white]recall[/bold white]: Contextual warnings surfaced on pre-commit / query\n"
        " 3. [bold white]memify / reflect[/bold white]: Consolidation of bug patterns into team rules\n"
        " 4. [bold white]forget[/bold white]: Explicit memory decay when code is refactored",
        title="Welcome",
        border_style="magenta"
    ))

    # ---------------------------------------------------------
    # Step 1: Init & Ingestion
    # ---------------------------------------------------------
    console.print(Rule("[bold cyan]Step 1: Setup & Ingestion (remember)[/bold cyan]"))
    client = MemoryClient(sample_dir)
    HookManager.install_pre_commit_hook(sample_dir)
    console.print("  [green]✓ Initialized Anamnesis in demo project.[/green]")
    console.print("  [green]✓ Cognee graph store created & pre-commit hook installed.[/green]")

    # ---------------------------------------------------------
    # Step 2: Ingest First Bug (remember)
    # ---------------------------------------------------------
    console.print(Rule("[bold cyan]Step 2: Log Historical Bug Fix (remember)[/bold cyan]"))
    bug1 = BugFixMemory(
        file_path="services/user_service.py",
        function_name="fetch_user_profile",
        title="Unchecked external API response crash",
        root_cause="Accessed response.json()['data']['profile'] directly without validating HTTP 200 status or checking if 'data' field existed",
        fix_description="Added status_code check and safe dict.get('data', {}).get('profile', {}) handling",
        severity="high",
        tags=["null-check", "user_service", "external-api"]
    )
    rec1 = client.remember_bug(bug1)
    console.print(f"  [bold green]✓ Logged Bug Memory (ID: {rec1.id})[/bold green]")
    console.print(f"    File: [cyan]{bug1.file_path}[/cyan]")
    console.print(f"    Root Cause: {bug1.root_cause}")

    # ---------------------------------------------------------
    # Step 3: Simulated Pre-Commit Recall (recall)
    # ---------------------------------------------------------
    console.print(Rule("[bold cyan]Step 3: Pre-Commit Memory Recall Warning (recall)[/bold cyan]"))
    console.print("[dim]Simulating developer editing services/payment_service.py with similar unchecked API call...[/dim]\n")
    
    query = "staged files: services/payment_service.py response.json() receipt status"
    recalled = client.recall(query, file_context="services/payment_service.py", top_k=2)
    
    if recalled:
        console.print("[bold yellow]⚠️  ANAMNESIS PRE-COMMIT HOOK DETECTED RELEVANT PAST BUG:[/bold yellow]")
        for rec in recalled:
            console.print(render_memory_warning(rec))

    # ---------------------------------------------------------
    # Step 4: Memory Reflection & Consolidation (memify)
    # ---------------------------------------------------------
    console.print(Rule("[bold cyan]Step 4: Memory Reflection & Consolidation (memify/reflect)[/bold cyan]"))
    console.print("[dim]Running 'anamnesis reflect' to cluster bug patterns into team rules...[/dim]\n")
    
    consolidator = MemoryConsolidator(client)
    new_rules = consolidator.reflect()
    
    rules = client.get_rules()
    render_rules_table(rules)

    # ---------------------------------------------------------
    # Step 5: Forgetting Stale Memories (forget)
    # ---------------------------------------------------------
    console.print(Rule("[bold cyan]Step 5: Decay Stale Memory on Refactor (forget)[/bold cyan]"))
    console.print(f"[dim]Developer refactored user_service.py. Forgetting memory ID {rec1.id}...[/dim]\n")
    
    removed = client.forget(rec1.id)
    console.print(f"  [bold green]✓ Cognee decay executed. Forgotten memory IDs: {removed}[/bold green]")

    # ---------------------------------------------------------
    # Step 6: Free-Form Memory Graph Q&A (ask)
    # ---------------------------------------------------------
    console.print(Rule("[bold cyan]Step 6: Free-Form Memory Q&A (ask)[/bold cyan]"))
    q = "Why do we validate external API responses in service layer?"
    records = client.recall(q, top_k=3)
    render_recall_response(q, records)

    # Dashboard
    console.print(Rule("[bold cyan]Demo Summary[/bold cyan]"))
    stats = {
        "total_memories": len(client.list_memories()),
        "bug_fixes": len(client.list_memories(MemoryType.BUG_FIX)),
        "rules": len(client.get_rules()),
        "commits": len(client.list_memories(MemoryType.COMMIT)),
        "hooks_installed": True,
        "backend": "Local SQLite + Cognee Memory Graph"
    }
    render_status_dashboard(stats)
    console.print("\n[bold green]✨ Demo Completed Successfully![/bold green]\n")

if __name__ == "__main__":
    run_full_demo()
