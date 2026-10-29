"""Rich-formatted interactive Command Line Interface for the AI Research Agent."""

import argparse
import json
import sys
from pathlib import Path

# Force UTF-8 stream handling on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.agent import ResearchAgent
from src.config import config, AgentConfig
from src.models import ResearchReport, ConfidenceLevel

console = Console()


def print_banner():
    banner_text = (
        "[bold cyan]Production-Oriented AI Research Agent[/bold cyan]\n"
        "[dim]Inspectable Planning • Tool Orchestration • Source Grounding • Resilience[/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))


def display_plan(plan):
    table = Table(title="[bold yellow]📋 Research Execution Plan[/bold yellow]", border_style="yellow")
    table.add_column("Step", justify="center", style="cyan", width=6)
    table.add_column("Objective", style="white", min_width=30)
    table.add_column("Tool", justify="center", style="magenta", width=16)
    table.add_column("Query / Target", style="dim", min_width=25)

    for step in plan.steps:
        table.add_row(
            str(step.step_id),
            step.objective,
            f"[{step.tool.value}]",
            step.query_or_target
        )
    console.print(table)


def display_sources(sources):
    table = Table(title="[bold green]📚 Verified Reference Sources[/bold green]", border_style="green")
    table.add_column("ID", justify="center", style="bold green", width=4)
    table.add_column("Title & Domain", style="white", min_width=30)
    table.add_column("URL", style="blue", min_width=25)
    table.add_column("Relevance", justify="center", style="cyan", width=10)

    for s in sources:
        domain_tag = f"([dim]{s.domain}[/dim])" if s.domain else ""
        table.add_row(
            f"[{s.source_id}]",
            f"{s.title} {domain_tag}",
            s.url,
            f"{int(s.relevance_score * 100)}%"
        )
    console.print(table)


def display_final_report(report: ResearchReport, judge_eval):
    console.print("\n")
    # Confidence badge color
    conf_color = "green" if report.confidence_level == ConfidenceLevel.HIGH else ("yellow" if report.confidence_level == ConfidenceLevel.MEDIUM else "red")

    summary_text = (
        f"[bold]Question:[/bold] {report.user_question}\n\n"
        f"[bold]Short Answer:[/bold]\n{report.short_answer}\n\n"
        f"[bold]Confidence Level:[/bold] [{conf_color}]{report.confidence_level.value}[/{conf_color}] "
        f"— [dim]{report.confidence_rationale}[/dim]\n"
        f"[bold]Grounding Audit:[/bold] [{conf_color}]{judge_eval.verdict} ({int(judge_eval.grounding_score * 100)}% grounded)[/{conf_color}] "
        f"— [dim]{judge_eval.audit_notes}[/dim]"
    )
    console.print(Panel(summary_text, title="[bold cyan]Executive Summary[/bold cyan]", border_style="cyan"))

    # Key Findings
    findings_md = "\n".join([f"- {f}" for f in report.key_findings])
    console.print(Panel(Markdown(findings_md), title="[bold green]Key Findings (Source-Grounded)[/bold green]", border_style="green"))

    # Sources
    if report.sources_used:
        display_sources(report.sources_used)

    # Limitations & Next Steps
    lim_text = "\n".join([f"• {l}" for l in report.limitations_or_assumptions])
    steps_text = "\n".join([f"• {s}" for s in report.suggested_next_steps])

    grid = Table.grid(expand=True)
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)
    grid.add_row(
        Panel(lim_text or "None noted.", title="[bold yellow]⚠️ Limitations & Assumptions[/bold yellow]", border_style="yellow"),
        Panel(steps_text or "None noted.", title="[bold blue]🚀 Suggested Next Steps[/bold blue]", border_style="blue")
    )
    console.print(grid)

    # Metadata & Performance
    meta = report.metadata
    meta_str = (
        f"⏱️  Duration: [bold]{meta.get('latency_seconds', 0)}s[/bold]  |  "
        f"🛠️  Tools Called: [bold]{meta.get('tool_calls_count', 0)}[/bold]  |  "
        f"⚡ Cache Hits: [bold]{meta.get('cache_hits_count', 0)}[/bold]  |  "
        f"🔍 Plan Steps: [bold]{meta.get('plan_steps_count', 0)}[/bold]  |  "
        f"🔖 Trace ID: [dim]{meta.get('trace_id', 'N/A')}[/dim]"
    )
    console.print(Panel(meta_str, title="[bold dim]Performance & Telemetry[/bold dim]", border_style="dim"))


def export_report_to_markdown(report: ResearchReport, filepath: Path):
    """Exports structured report as GitHub-flavored Markdown."""
    lines = [
        f"# Research Report: {report.user_question}",
        "",
        "## Executive Summary",
        f"{report.short_answer}",
        "",
        f"**Confidence Level:** {report.confidence_level.value}  ",
        f"**Confidence Rationale:** {report.confidence_rationale}",
        "",
        "## Key Findings",
        ""
    ]
    for kf in report.key_findings:
        lines.append(f"- {kf}")

    lines.extend([
        "",
        "## Sources Referenced",
        ""
    ])
    for s in report.sources_used:
        lines.append(f"- **[{s.source_id}] [{s.title}]({s.url})** ({s.domain})  \n  > {s.snippet}")

    lines.extend([
        "",
        "## Limitations and Assumptions",
        ""
    ])
    for lim in report.limitations_or_assumptions:
        lines.append(f"- {lim}")

    lines.extend([
        "",
        "## Suggested Next Steps",
        ""
    ])
    for step in report.suggested_next_steps:
        lines.append(f"- {step}")

    lines.extend([
        "",
        "---",
        "## Execution Telemetry",
        f"- **Latency:** {report.metadata.get('latency_seconds', 'N/A')}s",
        f"- **Tools Executed:** {report.metadata.get('tool_calls_count', 0)}",
        f"- **Grounding Score:** {int(report.metadata.get('grounding_score', 1.0) * 100)}%",
        f"- **Trace ID:** `{report.metadata.get('trace_id', '')}`",
        ""
    ])

    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    console.print(f"[green]✓ Markdown report exported to:[/green] {filepath}")


def export_report_to_json(report: ResearchReport, filepath: Path):
    """Exports report as formatted JSON."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))
    console.print(f"[green]✓ JSON report exported to:[/green] {filepath}")


def run_cli():
    parser = argparse.ArgumentParser(description="Production-Oriented AI Research Agent")
    parser.add_argument("query", nargs="?", help="Research question to investigate")
    parser.add_argument("--mock", action="store_true", help="Force deterministic mock mode (no API key required)")
    parser.add_argument("--export-md", type=str, help="File path to save Markdown report")
    parser.add_argument("--export-json", type=str, help="File path to save JSON report")
    parser.add_argument("--eval", action="store_true", help="Run the automated 5-query evaluation suite")

    args = parser.parse_args()

    if args.eval:
        from evaluation.eval_runner import run_evaluation_suite
        run_evaluation_suite()
        return

    print_banner()

    query = args.query
    if not query:
        console.print("[bold yellow]Enter your research question:[/bold yellow]")
        query = input("> ").strip()
        if not query:
            console.print("[red]Query cannot be empty. Exiting.[/red]")
            sys.exit(1)

    # Initialize configuration
    cfg = AgentConfig()
    if args.mock:
        cfg.mock_mode = True

    agent = ResearchAgent(cfg=cfg)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description="Initializing research agent...", total=None)

        def step_callback(phase, msg):
            progress.update(task, description=f"[{phase.upper()}] {msg}")

        report, plan, judge_eval, tracer = agent.run(query, on_step_callback=step_callback)

    # Display results
    if plan.steps:
        display_plan(plan)

    display_final_report(report, judge_eval)

    # Export if requested
    if args.export_md:
        export_report_to_markdown(report, Path(args.export_md))
    if args.export_json:
        export_report_to_json(report, Path(args.export_json))


if __name__ == "__main__":
    run_cli()
