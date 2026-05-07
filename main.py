"""
Multi-Agent Browser System — Main Entry Point
================================================
An AI-powered multi-agent system that can browse the web,
research topics, and compile structured reports.

Usage:
    python main.py                          # Interactive mode
    python main.py "your research query"    # Direct mode
"""

import asyncio
import sys
import os

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text

from config import Config
from agents.orchestrator import Orchestrator

console = Console()


def show_banner():
    """Display the startup banner."""
    banner = Text()
    banner.append("╔══════════════════════════════════════════════════╗\n", style="bright_blue")
    banner.append("║  ", style="bright_blue")
    banner.append("🤖 Multi-Agent Browser System", style="bold bright_white")
    banner.append("               ║\n", style="bright_blue")
    banner.append("║  ", style="bright_blue")
    banner.append("Powered by Gemma 4 (NVIDIA NIM) + Playwright", style="dim")
    banner.append("             ║\n", style="bright_blue")
    banner.append("╚══════════════════════════════════════════════════╝", style="bright_blue")
    console.print(banner)
    console.print()


def check_config():
    """Validate configuration before running."""
    if not Config.validate():
        console.print(Panel(
            "[red bold]NVIDIA_API_KEY not set![/red bold]\n\n"
            "1. Copy [cyan].env.example[/cyan] to [cyan].env[/cyan]\n"
            "2. Add your NVIDIA NIM API key\n"
            "3. Get a key at: [link]https://build.nvidia.com[/link]",
            title="⚠️ Configuration Error",
            border_style="red",
        ))
        return False
    return True


async def run_agent(prompt: str):
    """Run the multi-agent system with a prompt."""
    orchestrator = Orchestrator()
    report = await orchestrator.run(prompt)

    # Save report to file
    report_path = os.path.join(os.path.dirname(__file__), "report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Research Report\n\n**Query:** {prompt}\n\n---\n\n{report}")

    console.print(f"\n[dim]Report saved to: {report_path}[/dim]")
    return report


async def interactive_mode():
    """Run in interactive mode — prompt loop."""
    show_banner()

    if not check_config():
        return

    console.print("[dim]Type your research query, or 'quit' to exit.[/dim]\n")

    while True:
        try:
            prompt = Prompt.ask("[bold bright_blue]🔍 Enter your query[/bold bright_blue]")

            if prompt.lower() in ("quit", "exit", "q"):
                console.print("[dim]Goodbye! 👋[/dim]")
                break

            if not prompt.strip():
                continue

            await run_agent(prompt)
            console.print("\n" + "─" * 50 + "\n")

        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Goodbye! 👋[/dim]")
            break


async def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Direct mode: pass query as argument
        prompt = " ".join(sys.argv[1:])
        show_banner()
        if not check_config():
            return
        await run_agent(prompt)
    else:
        # Interactive mode
        await interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())
