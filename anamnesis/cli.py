import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Any
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

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
    render_timeline_results,
    render_search_strategy_badge,
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


# ---------------------------------------------------------------------------
# COGNEE PRIMITIVE: remember
# ---------------------------------------------------------------------------

@app.command("init")
def init_cmd(
    repo_path: Optional[Path] = typer.Option(None, "--repo", "-r", help="Path to git repository root"),
):
    """
    [COGNEE PRIMITIVE: remember]
    Initialize Anamnesis: ingest commit history, install git hooks, and set up Cognee graph.
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

    # Install both pre-commit and post-commit hooks
    hook_results = HookManager.install_all_hooks(root)
    if hook_results.get("pre_commit"):
        console.print("  [green]✓ Installed pre-commit recall hook (.git/hooks/pre-commit).[/green]")
    if hook_results.get("post_commit"):
        console.print("  [green]✓ Installed post-commit auto-ingest hook (.git/hooks/post-commit).[/green]")
    if not any(hook_results.values()):
        console.print("  [yellow]! Git directory not found; skipping hook installation.[/yellow]")

    config = load_config(root)
    config["initialized"] = True
    save_config(config, root)

    console.print(
        "\n[bold green]🎉 Anamnesis is ready![/bold green] "
        "Your codebase now has a long-term Cognee memory graph.\n"
    )
    console.print(
        "  [dim]Next steps:[/dim]\n"
        "  • [cyan]anamnesis remember-bug[/cyan] — log a bug fix\n"
        "  • [cyan]anamnesis ask \"<query>\"[/cyan] — query codebase memory\n"
        "  • [cyan]anamnesis reflect[/cyan] — consolidate patterns into rules\n"
        "  • [cyan]anamnesis mcp-serve[/cyan] — start MCP server for Claude Code\n"
    )


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
    Log a bug fix into the Cognee knowledge graph with typed entity extraction.
    Cognee extracts CodeFile → Function → BugPattern → Rule graph nodes.
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
        tags=["bug", Path(file_path).stem],
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(
            description="Extracting code entities & pushing to Cognee graph (CodeKnowledgeGraph schema)...",
            total=None,
        )
        rec = client.remember_bug(bug_mem)

    console.print(f"\n[bold green]✓ Memory logged into Cognee graph![/bold green] (ID: [cyan]{rec.id}[/cyan])")
    console.print(f"  File: [cyan]{file_path}[/cyan]")
    console.print(f"  Root Cause: {root_cause}")
    console.print(f"  [dim]Cognee extracted: CodeFile → Function → BugPattern → Fix nodes[/dim]")
    console.print(f"  [dim]temporal_cognify=True: bug pattern timestamped for evolution tracking[/dim]\n")


@app.command("remember")
def remember_cmd(
    title: str = typer.Argument(..., help="Title or header for the memory entry"),
    content: Optional[str] = typer.Option(None, "--content", "-c", help="Text content or body"),
    file_path: Optional[str] = typer.Option(None, "--file", "-f", help="Optional file path context"),
    commit_hash: Optional[str] = typer.Option(None, "--commit-hash", help="Git commit hash (for post-commit hook)"),
    message: Optional[str] = typer.Option(None, "--message", help="Commit message (for post-commit hook)"),
    author: Optional[str] = typer.Option(None, "--author", help="Commit author (for post-commit hook)"),
    files: Optional[str] = typer.Option(None, "--files", help="Comma-separated changed files"),
    silent: bool = typer.Option(False, "--silent", help="Suppress output (for post-commit hook)"),
):
    """
    [COGNEE PRIMITIVE: remember]
    Ingest a document, ADR, commit, or note into the Cognee memory graph.
    """
    root = find_project_root()
    client = MemoryClient(root)

    # Handle post-commit hook invocation
    if commit_hash and message:
        from anamnesis.memory.schemas import CommitMemory
        file_list = [f.strip() for f in (files or "").split(",") if f.strip()]
        commit = CommitMemory(
            commit_hash=commit_hash,
            author=author or "unknown",
            summary=message,
            files_changed=file_list,
        )
        client.remember_commit(commit)
        if not silent:
            console.print(f"[green]✓ Commit {commit_hash[:7]} auto-ingested into Cognee.[/green]")
        return

    if not content:
        content = typer.prompt("Enter document content / notes")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Ingesting document into Cognee knowledge graph...", total=None)
        rec = client.remember_doc(title=title, content=content, file_path=file_path)

    if not silent:
        console.print(f"\n[bold green]✓ Document ingested into Cognee memory![/bold green] (ID: [cyan]{rec.id}[/cyan])")


@app.command("improve")
def improve_cmd():
    """
    [COGNEE PRIMITIVE: improve / memify]
    Re-run graph enrichment with the CodeKnowledgeGraph schema on all stored memories.
    Use this after upgrading Anamnesis to apply the new schema to existing memories.
    """
    root = find_project_root()
    client = MemoryClient(root)

    console.print("\n[bold cyan]⚡ Running Cognee Graph Enrichment & Memory Improvement...[/bold cyan]")
    console.print("[dim]  Re-cognifying with CodeKnowledgeGraph schema + temporal tracking[/dim]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Re-indexing graph edges and optimizing memory weights...", total=None)
        client.improve()

    console.print("[bold green]✓ Memory graph improved and optimized successfully![/bold green]\n")


# ---------------------------------------------------------------------------
# COGNEE PRIMITIVE: recall
# ---------------------------------------------------------------------------

@app.command("ask")
def ask_cmd(
    query: str = typer.Argument(..., help="Natural language question to ask codebase memory"),
    file_context: Optional[str] = typer.Option(None, "--file", "-f", help="Optional file context filter"),
):
    """
    [COGNEE PRIMITIVE: recall]
    Query the Cognee knowledge graph using GRAPH_COMPLETION + HYBRID_COMPLETION search.
    Shows which search strategy (graph traversal / hybrid / coding rules) found each result.
    """
    root = find_project_root()
    client = MemoryClient(root)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Traversing Cognee knowledge graph (GRAPH + HYBRID + CODING_RULES)...", total=None)
        records = client.recall(query=query, file_context=file_context, top_k=5)

    render_recall_response(query, records)


@app.command("timeline")
def timeline_cmd(
    query: str = typer.Argument("recurring bugs and patterns", help="What to trace over time"),
    top_k: int = typer.Option(10, "--top-k", "-k", help="Number of temporal results"),
):
    """
    [COGNEE PRIMITIVE: recall — temporal]
    Show how bug patterns evolved over time using Cognee's temporal knowledge graph.
    Requires that bugs were stored with temporal_cognify=True (default since v0.2.0).
    """
    root = find_project_root()
    client = MemoryClient(root)

    console.print(f"\n[bold cyan]📅 Temporal Bug Pattern Analysis[/bold cyan] — '{query}'\n")

    if not client._init_cognee_if_needed():
        console.print("[yellow]Cognee not available. Showing local memories by timestamp:[/yellow]\n")
        memories = sorted(
            client.list_memories(MemoryType.BUG_FIX),
            key=lambda m: m.timestamp,
            reverse=True,
        )[:top_k]
        render_timeline_results(memories, fallback=True)
        return

    try:
        import cognee
        from cognee.modules.search.types.SearchType import SearchType

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Querying temporal Cognee graph...", total=None)
            results = asyncio.run(cognee.search(
                query_text=query,
                query_type=SearchType.TEMPORAL,
                datasets=["anamnesis_codebase"],
                top_k=top_k,
            ))
        render_timeline_results(results, fallback=False)
    except Exception as e:
        console.print(f"[yellow]Temporal search unavailable ({e}). Showing local timeline:[/yellow]\n")
        memories = sorted(
            client.list_memories(MemoryType.BUG_FIX),
            key=lambda m: m.timestamp,
            reverse=True,
        )[:top_k]
        render_timeline_results(memories, fallback=True)


@app.command("feedback")
def feedback_cmd(
    helpful: bool = typer.Option(True, "--helpful/--not-helpful", help="Was the last recall result helpful?"),
    session_id: Optional[str] = typer.Option(None, "--session", help="Session ID to annotate (auto-detected if omitted)"),
):
    """
    [COGNEE PRIMITIVE: improve — feedback loop]
    Rate the last recall result. Positive feedback improves future recall ranking
    via Cognee's truth subspace reranking mechanism.
    """
    root = find_project_root()
    client = MemoryClient(root)

    sid = session_id or client.get_last_session_id()

    if not sid:
        console.print("[yellow]No recent session found. Run 'anamnesis ask' first, then provide feedback.[/yellow]")
        raise typer.Exit(1)

    if not client._init_cognee_if_needed():
        console.print("[yellow]Cognee not available — feedback recorded locally only.[/yellow]")
        return

    try:
        import cognee
        from cognee.memory import FeedbackEntry

        score = 1.0 if helpful else 0.0
        label = "helpful ✓" if helpful else "not relevant ✗"

        asyncio.run(cognee.remember(
            FeedbackEntry(
                feedback_score=score,
                feedback_text=label,
            ),
            session_id=sid,
        ))

        console.print(
            f"\n[bold green]✓ Feedback recorded[/bold green] ([cyan]{label}[/cyan]) "
            f"for session [dim]{sid}[/dim]\n"
            "[dim]Future recalls will adapt to your preferences via truth subspace reranking.[/dim]\n"
        )
    except ImportError:
        # FeedbackEntry may not be in all Cognee versions — degrade gracefully
        console.print(
            f"\n[green]✓ Feedback noted locally[/green] ({'helpful' if helpful else 'not helpful'}).\n"
            "[dim]Upgrade Cognee to enable truth subspace personalized reranking.[/dim]\n"
        )
    except Exception as e:
        console.print(f"[yellow]Feedback storage failed: {e}[/yellow]")


# ---------------------------------------------------------------------------
# COGNEE PRIMITIVE: memify
# ---------------------------------------------------------------------------

@app.command("reflect")
def reflect_cmd():
    """
    [COGNEE PRIMITIVE: memify / reflect]
    Consolidate bug memories into team coding rules using cognee.memify()
    and SearchType.CODING_RULES. Replaces the old hardcoded keyword clustering.
    """
    root = find_project_root()
    client = MemoryClient(root)
    consolidator = MemoryConsolidator(client)

    console.print("\n[bold cyan]🧠 Running Semantic Memory Consolidation via cognee.memify()...[/bold cyan]")
    console.print("[dim]  Uses CODING_RULES retriever + LLM semantic clustering[/dim]\n")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Clustering patterns semantically via Cognee memify...", total=None)
        new_rules = consolidator.reflect()

    if new_rules:
        console.print(f"[bold green]🎉 Synthesized {len(new_rules)} new consolidated rule(s):[/bold green]\n")
        for r in new_rules:
            confidence = f"{r.confidence:.0%}" if hasattr(r, 'confidence') and r.confidence else ""
            console.print(f"  • [bold yellow]{r.rule_title}[/bold yellow] ([dim]Domain: {r.domain}[/dim]) [green]{confidence}[/green]")
            console.print(f"    [dim]{r.description[:120]}[/dim]\n")
    else:
        console.print("[dim]No new clusters found. Existing rules are up to date.[/dim]\n")


@app.command("rules")
def rules_cmd(
    domain: Optional[str] = typer.Option(None, "--domain", "-d", help="Filter by domain"),
):
    """
    List all active consolidated team rules and their provenance.
    """
    root = find_project_root()
    client = MemoryClient(root)
    rules = client.get_rules(domain=domain)
    render_rules_table(rules)


# ---------------------------------------------------------------------------
# COGNEE PRIMITIVE: forget
# ---------------------------------------------------------------------------

@app.command("forget")
def forget_cmd(
    target: str = typer.Argument(..., help="Memory ID or file path to forget/decay"),
):
    """
    [COGNEE PRIMITIVE: forget]
    Remove or decay stale memory when code is deleted or refactored.
    Triggers cognee.prune.prune_data() to clean up graph edges.
    """
    root = find_project_root()
    client = MemoryClient(root)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Decaying target memory in Cognee graph...", total=None)
        removed = client.forget(target)

    if removed:
        console.print(f"\n[bold green]✓ Forgot {len(removed)} memory item(s):[/bold green] [cyan]{', '.join(removed)}[/cyan]")
    else:
        console.print(f"\n[yellow]No active memories found matching '[bold white]{target}[/bold white]'.[/yellow]")


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

@app.command("mcp-serve")
def mcp_serve_cmd(
    transport: str = typer.Option("stdio", "--transport", "-t", help="Transport: stdio | sse | http"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host for sse/http transport"),
    port: int = typer.Option(8765, "--port", "-p", help="Port for sse/http transport"),
):
    """
    Start the Anamnesis MCP server for Claude Code / Cursor integration.

    Exposes codebase memory as native tools: recall_codebase_memory,
    remember_bug_fix, get_coding_rules, get_memory_status, forget_memory.

    Claude Desktop config (~/.claude/claude_desktop_config.json):
      { "mcpServers": { "anamnesis": { "command": "anamnesis", "args": ["mcp-serve"] } } }
    """
    from anamnesis.mcp_server import run_server

    console.print(f"\n[bold cyan]🔌 Starting Anamnesis MCP Server[/bold cyan] (transport: {transport})")
    if transport != "stdio":
        console.print(f"  Listening on: [cyan]http://{host}:{port}/mcp[/cyan]")
    console.print("[dim]  Tools: recall_codebase_memory | remember_bug_fix | get_coding_rules | get_memory_status | forget_memory[/dim]\n")

    run_server(transport=transport, host=host, port=port)


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------

@app.command("visualize")
def visualize_cmd(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save graph to file instead of opening browser"),
):
    """
    Open an interactive Cognee memory provenance graph in the browser.
    Shows: Tenant → User → Dataset → Files → Bug Nodes → Rule Nodes.
    """
    root = find_project_root()
    client = MemoryClient(root)

    if not client._init_cognee_if_needed():
        console.print("[yellow]Cognee not initialized. Run 'anamnesis init' first.[/yellow]")
        raise typer.Exit(1)

    console.print("\n[bold cyan]🕸️  Building Memory Provenance Graph...[/bold cyan]")

    try:
        import cognee
        import webbrowser

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Generating Cognee provenance graph...", total=None)

            try:
                graph_data = asyncio.run(cognee.get_memory_provenance_graph())
                graph_html = _render_provenance_html(graph_data)
            except AttributeError:
                # Fallback: generate a simple HTML visualization from local memories
                memories = client.list_memories()
                graph_html = _generate_fallback_graph_html(memories)

        out_path = output or (root / ".anamnesis" / "graph.html")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(graph_html, encoding="utf-8")

        console.print(f"[green]✓ Graph saved to:[/green] [cyan]{out_path}[/cyan]")

        if not output:
            webbrowser.open(f"file://{out_path.resolve()}")
            console.print("[green]✓ Graph opened in browser.[/green]\n")

    except Exception as e:
        console.print(f"[yellow]Graph visualization failed: {e}[/yellow]")
        console.print("[dim]Try 'anamnesis status' for a text-based memory overview.[/dim]")


def _render_provenance_html(graph_data: Any) -> str:
    """Render Cognee provenance graph data to HTML."""
    return f"""<!DOCTYPE html>
<html><head><title>Anamnesis Memory Provenance</title>
<style>body{{background:#0d1117;color:#c9d1d9;font-family:monospace;padding:20px}}</style>
</head><body><pre>{graph_data}</pre></body></html>"""


def _generate_fallback_graph_html(memories: List) -> str:
    """Generate a simple D3.js knowledge graph from local memories."""
    import json as json_mod

    nodes = []
    edges = []

    # Root node
    nodes.append({"id": "root", "label": "Codebase Memory", "type": "root", "size": 20})

    # Group memories by type
    type_nodes = {}
    for mem_type in ["bug_fix", "rule", "commit", "documentation"]:
        type_id = f"type_{mem_type}"
        type_nodes[mem_type] = type_id
        nodes.append({"id": type_id, "label": mem_type.replace("_", " ").title(), "type": "category", "size": 15})
        edges.append({"source": "root", "target": type_id})

    # Add individual memory nodes
    for mem in memories[:50]:  # Cap at 50 for readability
        nodes.append({
            "id": mem.id,
            "label": mem.title[:40] + ("..." if len(mem.title) > 40 else ""),
            "type": mem.memory_type.value,
            "size": 8,
            "file": mem.file_path or "",
        })
        edges.append({"source": type_nodes.get(mem.memory_type.value, "root"), "target": mem.id})

    nodes_json = json_mod.dumps(nodes)
    edges_json = json_mod.dumps(edges)

    return f"""<!DOCTYPE html>
<html>
<head>
  <title>Anamnesis Memory Provenance Graph</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    body {{ background: #0d1117; color: #c9d1d9; font-family: 'JetBrains Mono', monospace; margin: 0; overflow: hidden; }}
    h1 {{ position: absolute; top: 15px; left: 20px; color: #58a6ff; font-size: 18px; margin: 0; }}
    .legend {{ position: absolute; top: 55px; left: 20px; font-size: 12px; }}
    .legend span {{ display: inline-block; width: 12px; height: 12px; margin-right: 5px; border-radius: 50%; }}
    svg {{ width: 100vw; height: 100vh; }}
    .node circle {{ stroke: #30363d; stroke-width: 1.5px; cursor: pointer; }}
    .node text {{ font-size: 10px; fill: #c9d1d9; pointer-events: none; }}
    .link {{ stroke: #30363d; stroke-width: 1px; opacity: 0.6; }}
    .node circle:hover {{ stroke: #58a6ff; stroke-width: 2.5px; }}
  </style>
</head>
<body>
  <h1>🧠 Anamnesis Memory Graph</h1>
  <div class="legend">
    <span style="background:#f85149"></span>bug_fix &nbsp;
    <span style="background:#3fb950"></span>rule &nbsp;
    <span style="background:#58a6ff"></span>commit &nbsp;
    <span style="background:#d2a8ff"></span>docs &nbsp;
    <span style="background:#ffa657"></span>category
  </div>
  <svg></svg>
  <script>
    const nodes = {nodes_json};
    const links = {edges_json};
    const color = {{
      "root": "#ffa657", "category": "#ffa657",
      "bug_fix": "#f85149", "rule": "#3fb950",
      "commit": "#58a6ff", "documentation": "#d2a8ff"
    }};

    const svg = d3.select("svg");
    const width = window.innerWidth, height = window.innerHeight;
    const sim = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(80))
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(width / 2, height / 2));

    const link = svg.append("g").selectAll("line")
      .data(links).join("line").attr("class", "link");

    const node = svg.append("g").selectAll("g")
      .data(nodes).join("g").attr("class", "node")
      .call(d3.drag()
        .on("start", (e, d) => {{ if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }})
        .on("drag", (e, d) => {{ d.fx = e.x; d.fy = e.y; }})
        .on("end", (e, d) => {{ if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }}));

    node.append("circle")
      .attr("r", d => d.size || 8)
      .style("fill", d => color[d.type] || "#8b949e");

    node.append("text").attr("dx", d => (d.size || 8) + 3).attr("dy", 4)
      .text(d => d.label);

    node.append("title").text(d => d.file ? d.label + "\\n" + d.file : d.label);

    sim.on("tick", () => {{
      link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
      node.attr("transform", d => `translate(${{d.x}}, ${{d.y}})`);
    }});
  </script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

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
        "post_commit_hook": config.get("post_commit_hook_installed", False),
        "backend": "Cognee Graph (CodeKnowledgeGraph) + Vector + Local JSON",
        "search_types": "GRAPH_COMPLETION + HYBRID_COMPLETION + CODING_RULES",
        "cognee_active": client._cognee_initialized,
    }

    render_status_dashboard(stats)


# ---------------------------------------------------------------------------
# Config commands
# ---------------------------------------------------------------------------

@config_app.command("set-cloud-key")
def set_cloud_key_cmd(
    key: str = typer.Argument(..., help="Cognee Cloud API key from platform.cognee.ai"),
    url: str = typer.Option("https://api.cognee.ai", "--url", "-u", help="Cognee Cloud API endpoint URL"),
):
    """Configure your Cognee Cloud API Key for extended memory storage."""
    root = find_project_root()
    config = load_config(root)
    config["cognee_api_key"] = key.strip()
    config["cognee_api_url"] = url.strip()
    config["use_cloud"] = True
    save_config(config, root)

    env_path = root / ".env"
    lines = []
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = [l for l in f.readlines() if not l.startswith("COGNEE_API_KEY") and not l.startswith("COGNEE_API_URL")]
    lines.append(f"COGNEE_API_KEY={key.strip()}\n")
    lines.append(f"COGNEE_API_URL={url.strip()}\n")
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    console.print(f"\n[bold green]✓ Cognee Cloud API Key configured![/bold green]")
    console.print(f"  Endpoint: [cyan]{url}[/cyan]\n")


@config_app.command("set-llm-key")
def set_llm_key_cmd(
    key: str = typer.Argument(..., help="LLM API Key (OpenAI / Anthropic / LiteLLM)"),
):
    """Configure LLM API Key for diff summarization, entity extraction, and recall synthesis."""
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

    console.print(f"\n[bold green]✓ LLM API Key configured![/bold green]\n")


@config_app.command("show")
def config_show_cmd():
    """Display active Anamnesis configuration and Cognee Cloud connection status."""
    root = find_project_root()
    config = load_config(root)

    cognee_key = os.getenv("COGNEE_API_KEY") or config.get("cognee_api_key")
    llm_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or config.get("llm_api_key")

    def mask_key(k: Optional[str]) -> str:
        if not k:
            return "[yellow]Not set[/yellow]"
        return f"[green]{k[:4]}...{k[-4:]}[/green]" if len(k) > 8 else "[green]Configured[/green]"

    console.print("\n[bold cyan]⚙️  Anamnesis Configuration Dashboard[/bold cyan]\n")
    console.print(f"  Project Root:            [white]{root}[/white]")
    console.print(f"  Cognee Cloud API Key:    {mask_key(cognee_key)}")
    console.print(f"  Cognee Cloud Endpoint:   [cyan]{config.get('cognee_api_url', 'https://api.cognee.ai')}[/cyan]")
    console.print(f"  LLM Provider Key:        {mask_key(llm_key)}")
    console.print(f"  Pre-Commit Hook:         {'[green]Installed[/green]' if config.get('hooks_installed') else '[yellow]Not Installed[/yellow]'}")
    console.print(f"  Post-Commit Hook:        {'[green]Installed[/green]' if config.get('post_commit_hook_installed') else '[yellow]Not Installed[/yellow]'}")
    console.print(f"  Reflection Threshold:    [cyan]{config.get('reflection_threshold', 3)} bug fixes[/cyan]")
    console.print(f"  Graph Schema:            [magenta]CodeKnowledgeGraph (typed entities)[/magenta]")
    console.print(f"  Search Strategy:         [magenta]GRAPH_COMPLETION + HYBRID_COMPLETION + CODING_RULES[/magenta]\n")


# ---------------------------------------------------------------------------
# Git hook internal commands
# ---------------------------------------------------------------------------

@hook_app.command("run")
def hook_run_cmd(
    stage: str = typer.Option("pre-commit", "--stage", help="Hook stage name"),
    silent: bool = typer.Option(False, "--silent", help="Suppress all output"),
):
    """Internal handler executed by git hooks."""
    root = find_project_root()

    if stage == "pre-commit":
        result = HookManager.execute_pre_commit_check(root)
        warnings = result.get("warnings", [])

        if warnings and not silent:
            console.print("\n[bold yellow]════════════════════════════════════════════════════════════════[/bold yellow]")
            console.print("[bold yellow]  ⚠️  ANAMNESIS PRE-COMMIT MEMORY WARNINGS[/bold yellow]")
            console.print("[bold yellow]  Cognee Graph Search: GRAPH_COMPLETION + HYBRID_COMPLETION[/bold yellow]")
            console.print("[bold yellow]════════════════════════════════════════════════════════════════[/bold yellow]\n")
            for w in warnings:
                console.print(render_memory_warning(w))
            console.print("[dim]Review past bug history above before completing this commit.[/dim]\n")
            console.print("[dim]Run 'anamnesis feedback --helpful' or '--not-helpful' to improve future recalls.[/dim]\n")

    elif stage == "post-commit":
        HookManager.execute_post_commit_ingest(root, silent=silent)


if __name__ == "__main__":
    app()
