from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.style import Style
from rich.markdown import Markdown
from rich.columns import Columns
from anamnesis.memory.schemas import MemoryRecord, MemoryType

console = Console()

def render_banner() -> None:
    banner_text = r"""[bold cyan]
   ___                      __                 
  / _ | ___  ___ ___ _  ___/ /_ _____  ___ _____
 / __ |/ _ \/ _ `/  ' \/ _  / __/ __/ / _ `/ _  /
/_/ |_/_//_/\_,_/_/_/_/\_,_/\__/\__/  \_, /\_,_/ 
                                     /___/       
[/bold cyan]
[bold white]Codebase Memory Companion[/bold white] [dim]powered by Cognee AI[/dim]
"""
    console.print(banner_text)

def render_memory_warning(record: MemoryRecord) -> Panel:
    file_info = f"[cyan]{record.file_path}[/cyan]" if record.file_path else "[dim]General[/dim]"
    type_badge = f"[bold yellow]{record.memory_type.value.upper()}[/bold yellow]"
    
    body = Text()
    body.append(f"Title: ", style="bold white")
    body.append(f"{record.title}\n", style="bold yellow")
    body.append(f"Scope: {file_info}\n\n", style="dim")
    body.append(record.content, style="bright_white")
    
    return Panel(
        body,
        title=f"⚠️ Memory Recall Warning [{type_badge}] (ID: {record.id})",
        border_style="yellow",
        expand=True
    )

def render_recall_response(query: str, records: List[MemoryRecord]) -> None:
    console.print(f"\n[bold cyan]🔍 Memory Recall for Query:[/bold cyan] [italic]\"{query}\"[/italic]\n")
    if not records:
        console.print(Panel("[dim]No relevant past memories found in Cognee graph.[/dim]", border_style="dim"))
        return

    for i, rec in enumerate(records, 1):
        file_badge = f" 📁 [cyan]{rec.file_path}[/cyan]" if rec.file_path else ""
        panel_title = f"[bold green]#{i} Memory Match[/bold green] [dim]({rec.id})[/dim]{file_badge}"
        
        content_text = Text()
        content_text.append(f"Type: {rec.memory_type.value}\n", style="dim green")
        content_text.append(rec.content)
        
        console.print(Panel(content_text, title=panel_title, border_style="green"))

def render_rules_table(rules: List[MemoryRecord]) -> None:
    if not rules:
        console.print(Panel("[dim]No consolidated rules registered. Run 'anamnesis reflect' to aggregate patterns.[/dim]", border_style="dim"))
        return

    table = Table(title="🧠 Consolidated Team Rules & Coding Conventions", border_style="cyan")
    table.add_column("ID", style="dim cyan", no_wrap=True)
    table.add_column("Rule Title", style="bold white")
    table.add_column("Domain", style="magenta")
    table.add_column("Provenance & Observed Files", style="green")
    table.add_column("Confidence", style="bold yellow")

    for rule in rules:
        meta = rule.metadata or {}
        provenance = ", ".join(meta.get("provenance_files", [])) or "Global"
        conf = f"{float(meta.get('confidence', 0.9)):.0%}"
        table.add_row(
            rule.id,
            rule.title,
            meta.get("domain", "services"),
            provenance,
            conf
        )

    console.print(table)

def render_status_dashboard(stats: Dict[str, Any]) -> None:
    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_column()

    stats_table = Table(title="📊 Anamnesis Memory Graph Status", border_style="cyan")
    stats_table.add_column("Metric", style="bold white")
    stats_table.add_column("Value", style="bold cyan")

    stats_table.add_row("Total Active Memories", str(stats.get("total_memories", 0)))
    stats_table.add_row("Bug Fix Records", str(stats.get("bug_fixes", 0)))
    stats_table.add_row("Consolidated Rules", str(stats.get("rules", 0)))
    stats_table.add_row("Git Commit Memories", str(stats.get("commits", 0)))
    stats_table.add_row("Git Pre-commit Hook", "[green]Installed[/green]" if stats.get("hooks_installed") else "[yellow]Not Installed[/yellow]")
    stats_table.add_row("Cognee Graph Backend", stats.get("backend", "Local SQLite + Vector Index"))

    console.print(stats_table)
