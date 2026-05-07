"""
Rich-powered logging for the multi-agent browser system.
Provides beautiful, color-coded console output for each agent.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich.markdown import Markdown
from rich import box


console = Console()

# Agent color mapping
AGENT_COLORS = {
    "orchestrator": "bold bright_blue",
    "planner": "bold green",
    "browser": "bold yellow",
    "reader": "bold red",
    "executor": "bold magenta",
    "verifier": "bold cyan",
    "system": "bold white",
}

AGENT_ICONS = {
    "orchestrator": "🧠",
    "planner": "📋",
    "browser": "🌐",
    "reader": "📖",
    "executor": "⚡",
    "verifier": "✅",
    "system": "⚙️",
}


class AgentLogger:
    """Beautiful logging for each agent in the system."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.color = AGENT_COLORS.get(agent_name, "white")
        self.icon = AGENT_ICONS.get(agent_name, "🔹")

    def info(self, message: str):
        """Log an info message."""
        console.print(
            f"  {self.icon} [{self.color}][{self.agent_name.upper()}][/{self.color}] {message}"
        )

    def success(self, message: str):
        """Log a success message."""
        console.print(
            f"  ✅ [{self.color}][{self.agent_name.upper()}][/{self.color}] [green]{message}[/green]"
        )

    def error(self, message: str):
        """Log an error message."""
        console.print(
            f"  ❌ [{self.color}][{self.agent_name.upper()}][/{self.color}] [red]{message}[/red]"
        )

    def warning(self, message: str):
        """Log a warning message."""
        console.print(
            f"  ⚠️  [{self.color}][{self.agent_name.upper()}][/{self.color}] [yellow]{message}[/yellow]"
        )

    def step(self, step_num: int, total: int, message: str):
        """Log a step progress message."""
        console.print(
            f"  {self.icon} [{self.color}][{self.agent_name.upper()}][/{self.color}] "
            f"[dim]Step {step_num}/{total}[/dim] → {message}"
        )

    def data(self, title: str, content: str):
        """Log extracted data in a panel."""
        panel = Panel(
            content[:500] + ("..." if len(content) > 500 else ""),
            title=f"{self.icon} {title}",
            border_style=self.color.replace("bold ", ""),
            padding=(1, 2),
        )
        console.print(panel)

    @staticmethod
    def plan_table(steps: list):
        """Display the plan as a beautiful table."""
        table = Table(
            title="📋 Execution Plan",
            box=box.ROUNDED,
            show_lines=True,
            title_style="bold bright_green",
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Action", style="cyan", width=16)
        table.add_column("Description", style="white", width=40)
        table.add_column("Target", style="yellow", width=30)
        table.add_column("Status", width=10)

        status_icons = {
            "pending": "⏳",
            "running": "🔄",
            "success": "✅",
            "failed": "❌",
            "skipped": "⏭️",
        }

        for step in steps:
            status = step.get("status", "pending") if isinstance(step, dict) else step.status.value
            icon = status_icons.get(status, "⏳")
            
            if isinstance(step, dict):
                table.add_row(
                    str(step.get("id", "")),
                    step.get("action", ""),
                    step.get("description", "")[:40],
                    step.get("target", "")[:30],
                    icon,
                )
            else:
                table.add_row(
                    str(step.id),
                    step.action.value,
                    step.description[:40],
                    step.target[:30],
                    icon,
                )

        console.print(table)

    @staticmethod
    def final_report(report: str):
        """Display the final report."""
        console.print()
        console.print(Panel(
            Markdown(report),
            title="📊 Final Report",
            border_style="bright_magenta",
            padding=(1, 2),
            expand=True,
        ))

    @staticmethod
    def header():
        """Display the system header."""
        console.print()
        console.print(Panel(
            Text.from_markup(
                "[bold bright_blue]Multi-Agent Browser System[/bold bright_blue]\n"
                "[dim]Powered by Gemini AI + Playwright[/dim]"
            ),
            border_style="bright_blue",
            padding=(1, 2),
        ))
        console.print()

    @staticmethod
    def divider(text: str = ""):
        """Print a divider."""
        if text:
            console.rule(f"[bold]{text}[/bold]", style="dim")
        else:
            console.rule(style="dim")
