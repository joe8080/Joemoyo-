#!/usr/bin/env python3
"""
JoeMoyo Business Agent System
==============================
AI agents for your YouTube channels, music studio, and Shopify store.

Usage:
  python main.py history  --topic "The Fall of Constantinople"
  python main.py finance  --topic "Bitcoin ETF Analysis"
  python main.py shopify  --report weekly
  python main.py leads    --type studio --name "Artist Name" --genre "R&B"
  python main.py leads    --type sponsor --name "Brand Name" --channel history
  python main.py market   --brand history_channel --topic "New video out now"
  python main.py ideas    --weeks 4
"""

import sys
import click
from rich.console import Console
from rich.panel import Panel

console = Console()


def get_orchestrator():
    """Lazy-load orchestrator to show errors clearly."""
    try:
        from orchestrator.orchestrator import BusinessOrchestrator
        return BusinessOrchestrator()
    except EnvironmentError as e:
        console.print(f"[bold red]Setup Error:[/bold red] {e}")
        console.print("\n[dim]Steps to fix:")
        console.print("  1. Copy .env.example to .env")
        console.print("  2. Add your ANTHROPIC_API_KEY")
        console.print("  3. Run the command again[/dim]")
        sys.exit(1)


@click.group()
def cli():
    """
    \b
    JoeMoyo Business Agent System
    Powered by Claude AI
    """
    console.print(Panel(
        "[bold cyan]JoeMoyo Business Agent System[/bold cyan]\n"
        "[dim]Powered by Claude claude-sonnet-4-6[/dim]",
        style="cyan",
        padding=(0, 2),
    ))


# ------------------------------------------------------------------ #
#  HISTORY CHANNEL                                                     #
# ------------------------------------------------------------------ #

@cli.command()
@click.option(
    "--topic", "-t",
    required=True,
    help='Historical topic (e.g. "The Fall of Rome")',
)
@click.option(
    "--script-only",
    is_flag=True,
    help="Skip research, write script from Claude knowledge only",
)
def history(topic: str, script_only: bool):
    """
    Produce a complete historical YouTube video package.

    Runs: Research → Script → Social Media Bundle
    Outputs saved to outputs/scripts/ and outputs/marketing/
    """
    orch = get_orchestrator()
    if script_only:
        console.print(f"[bold]Writing script for:[/bold] {topic}")
        result = orch.script_history.write_script(topic_or_research=topic)
        console.print(result)
    else:
        result = orch.produce_history_video(topic)
        console.print(f"\n[bold green]Done![/bold green] Script: {len(result['script'].split())} words")


# ------------------------------------------------------------------ #
#  FINANCE CHANNEL                                                     #
# ------------------------------------------------------------------ #

@cli.command()
@click.option(
    "--topic", "-t",
    required=True,
    help='Financial topic (e.g. "Bitcoin ETF Analysis")',
)
@click.option(
    "--ideas-only",
    is_flag=True,
    help="Generate video ideas instead of a full analysis",
)
@click.option(
    "--count",
    default=10,
    show_default=True,
    help="Number of ideas to generate (used with --ideas-only)",
)
def finance(topic: str, ideas_only: bool, count: int):
    """
    Produce financial YouTube content.

    Runs: Financial Research → Script → Social Media Bundle
    Or: Generate video ideas list (with --ideas-only)
    """
    orch = get_orchestrator()
    if ideas_only:
        console.print(f"[bold]Generating {count} video ideas for:[/bold] {topic}")
        result = orch.financial_agent.generate_video_ideas(niche=topic, count=count)
        console.print(result)
    else:
        result = orch.produce_finance_video(topic)
        console.print(f"\n[bold green]Done![/bold green] Script: {len(result['script'].split())} words")


# ------------------------------------------------------------------ #
#  SHOPIFY REPORTING                                                   #
# ------------------------------------------------------------------ #

@cli.command()
@click.option(
    "--report", "-r",
    default="weekly",
    type=click.Choice(["weekly", "monthly"]),
    show_default=True,
    help="Report type",
)
def shopify(report: str):
    """
    Generate Shopify store performance reports.

    Requires: SHOPIFY_SHOP_NAME and SHOPIFY_ACCESS_TOKEN in .env
    Outputs saved to outputs/reports/
    """
    orch = get_orchestrator()
    try:
        if report == "weekly":
            result = orch.weekly_shopify_report()
        else:
            result = orch.monthly_shopify_report()
        console.print(result)
    except EnvironmentError as e:
        console.print(f"[bold red]Shopify Error:[/bold red] {e}")
        sys.exit(1)


# ------------------------------------------------------------------ #
#  LEAD GENERATION                                                     #
# ------------------------------------------------------------------ #

@cli.command()
@click.option(
    "--type", "lead_type",
    required=True,
    type=click.Choice(["studio", "sponsor"]),
    help="studio = music studio client | sponsor = YouTube sponsorship",
)
@click.option("--name", "-n", required=True, help="Prospect/brand name")
@click.option("--genre", default="", help="Music genre (for studio leads)")
@click.option("--followers", default="", help="Social media following size")
@click.option("--industry", default="", help="Industry (for sponsorship leads)")
@click.option(
    "--channel",
    default="history_channel",
    type=click.Choice(["history_channel", "finance_channel"]),
    help="Which channel to pitch for (sponsor only)",
)
def leads(lead_type: str, name: str, genre: str, followers: str, industry: str, channel: str):
    """
    Generate sales outreach sequences.

    For music studio: cold email sequence to book recording clients.
    For sponsors: YouTube sponsorship pitch package.

    Outputs saved to outputs/leads/
    """
    orch = get_orchestrator()
    if lead_type == "studio":
        prospect = {"name": name, "genre": genre, "followers": followers}
        result = orch.studio_outreach(prospect)
    else:
        brand_info = {"name": name, "industry": industry}
        result = orch.sponsorship_pitch(brand_info, channel=channel)
    console.print(result)


# ------------------------------------------------------------------ #
#  MARKETING CONTENT                                                   #
# ------------------------------------------------------------------ #

@cli.command()
@click.option(
    "--brand", "-b",
    required=True,
    type=click.Choice(["history_channel", "finance_channel", "music_studio", "shopify_store"]),
    help="Which brand to create content for",
)
@click.option("--topic", "-t", required=True, help="Content topic or angle")
@click.option(
    "--type", "content_type",
    default="social",
    type=click.Choice(["social", "email", "ads"]),
    show_default=True,
    help="Type of content to generate",
)
def market(brand: str, topic: str, content_type: str):
    """
    Generate marketing content for any brand.

    social = Social media bundle (all platforms)
    email  = Full email newsletter
    ads    = Ad copy variations

    Outputs saved to outputs/marketing/
    """
    orch = get_orchestrator()
    if content_type == "social":
        result = orch.marketing_agent.create_social_bundle(brand, topic)
    elif content_type == "email":
        result = orch.marketing_agent.write_email_newsletter(brand, topic)
    else:
        result = orch.marketing_agent.write_ad_copy(brand, topic)
    console.print(result)


# ------------------------------------------------------------------ #
#  CONTENT CALENDAR                                                    #
# ------------------------------------------------------------------ #

@cli.command()
@click.option(
    "--weeks", "-w",
    default=4,
    show_default=True,
    help="Number of weeks to plan",
)
def ideas(weeks: int):
    """
    Generate a content ideas calendar for all YouTube channels.

    Outputs video ideas for both history and finance channels.
    Outputs saved to outputs/scripts/
    """
    orch = get_orchestrator()
    result = orch.generate_content_calendar(weeks=weeks)
    console.print("\n[bold]HISTORY CHANNEL IDEAS[/bold]")
    console.print(result["history_channel_ideas"])
    console.print("\n[bold]FINANCE CHANNEL IDEAS[/bold]")
    console.print(result["finance_channel_ideas"])


if __name__ == "__main__":
    cli()
