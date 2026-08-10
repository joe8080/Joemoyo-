"""
BusinessOrchestrator: Wires all agents together into end-to-end workflows.

Each workflow method represents a real business task that chains multiple agents.
The orchestrator itself is NOT an AI agent — it is deterministic Python that
sequences agent calls and passes outputs between them.
"""

from rich.console import Console
from rich.panel import Panel

from agents.content_research import ContentResearchAgent
from agents.script_writer import ScriptWriterAgent
from agents.financial_content import FinancialContentAgent
from agents.marketing import MarketingAgent
from agents.lead_generator import LeadGeneratorAgent

console = Console()


class BusinessOrchestrator:
    """Top-level orchestrator for all JoeMoyo business workflows."""

    def __init__(self):
        self.research_agent = ContentResearchAgent()
        self.script_history = ScriptWriterAgent(channel="history_channel")
        self.script_finance = ScriptWriterAgent(channel="finance_channel")
        self.financial_agent = FinancialContentAgent()
        self.marketing_agent = MarketingAgent()
        self.lead_agent = LeadGeneratorAgent()

    # ------------------------------------------------------------------ #
    #  WORKFLOW 1: Full Historical YouTube Video Production Pipeline       #
    # ------------------------------------------------------------------ #

    def produce_history_video(self, topic: str) -> dict:
        """
        Full pipeline: Research → Script → Social Media Bundle.

        Args:
            topic: The historical topic (e.g. "The Fall of Constantinople")

        Returns: dict with research, script, and social_bundle
        """
        console.print(Panel(
            f"[bold]History Video Pipeline[/bold]\nTopic: {topic}",
            style="blue",
        ))

        console.print("\n[bold][Step 1/3][/bold] Researching topic...")
        research = self.research_agent.research_topic(topic)

        console.print("\n[bold][Step 2/3][/bold] Writing script...")
        script = self.script_history.write_script(
            topic_or_research=research["research"],
            target_minutes=12,
        )

        console.print("\n[bold][Step 3/3][/bold] Creating social media bundle...")
        social_bundle = self.marketing_agent.create_social_bundle(
            brand="history_channel",
            topic=f"New YouTube video: {topic}",
        )

        console.print(Panel("[bold green]History video pipeline complete![/bold green]", style="green"))
        return {
            "topic": topic,
            "research": research["research"],
            "script": script,
            "social_bundle": social_bundle,
        }

    # ------------------------------------------------------------------ #
    #  WORKFLOW 1b: OrigineX (OGX) Evidence-Gated Video Pipeline           #
    # ------------------------------------------------------------------ #

    def produce_ogx_video(
        self,
        topic: str,
        style: str = "archives",
        target_minutes: int = 0,
        skip_research: bool = False,
        allow_unverified: bool = False,
        persist: bool = True,
    ) -> dict:
        """
        Full OrigineX pipeline: Research → Script → Video Build → Packaging.

        Unlike the other content workflows, this one is evidence-gated: it
        refuses to start unless the OGX research database is reachable, because
        every OGX claim is verified against it before shipping. Pass
        allow_unverified=True to run on Claude's trained knowledge instead —
        output is then marked unverified throughout.

        Args:
            topic:            Subject (e.g. "Queen Nzinga" or "Operation Condor")
            style:            "archives" (default house style) or "declassified"
            target_minutes:   Runtime target; defaults to 18 / 42 by style
            skip_research:    Go straight to script from the topic alone
            allow_unverified: Run without the research database
            persist:          Log the episode and every agent output to the database

        Returns: dict with research, script, build_sheet, packaging, episode_id
        """
        from agents.ogx_packaging import OGXPackagingAgent
        from agents.ogx_research import OGXResearchAgent
        from agents.ogx_script import OGXScriptWriterAgent
        from agents.ogx_video_build import OGXVideoBuildAgent
        from tools import ogx_db

        if not allow_unverified:
            ogx_db.require_enabled()

        if not target_minutes:
            target_minutes = 42 if style == "declassified" else 18

        total_steps = 3 if skip_research else 4
        console.print(Panel(
            f"[bold]OGX Video Pipeline[/bold]\n"
            f"Topic: {topic}\n"
            f"Style: {style} · Target: {target_minutes} min"
            + ("\n[yellow]UNVERIFIED MODE — no database gate[/yellow]"
               if allow_unverified else ""),
            style="yellow",
        ))

        episode_id = ""
        if persist and not allow_unverified:
            episode_id = ogx_db.create_episode(
                title=topic, topic=topic, target_minutes=target_minutes,
            )
            if episode_id:
                console.print(f"[dim]Episode {episode_id} opened in video_episodes[/dim]")

        def record(role: str, content: str) -> None:
            if episode_id:
                ogx_db.save_agent_output(episode_id, role, content, model=self._ogx_model())

        step = 0
        research = ""
        if not skip_research:
            step += 1
            console.print(f"\n[bold][Step {step}/{total_steps}][/bold] Researching (database first)...")
            researcher = OGXResearchAgent(allow_unverified=allow_unverified)
            research = researcher.research_topic(topic)["research"]
            record("research", research)

        step += 1
        console.print(f"\n[bold][Step {step}/{total_steps}][/bold] Writing {style} script...")
        writer = OGXScriptWriterAgent(style=style, allow_unverified=allow_unverified)
        script = writer.write_script(
            topic_or_research=research or topic,
            target_minutes=target_minutes,
        )
        record("script", script)

        step += 1
        console.print(f"\n[bold][Step {step}/{total_steps}][/bold] Building the shot sheet...")
        builder = OGXVideoBuildAgent(allow_unverified=allow_unverified)
        build_sheet = builder.build_sheet(script, target_minutes=target_minutes, subject=topic)
        record("visual", build_sheet)  # the schema's role vocabulary for build work

        step += 1
        console.print(f"\n[bold][Step {step}/{total_steps}][/bold] Packaging for publication...")
        packager = OGXPackagingAgent(allow_unverified=allow_unverified)
        packaging = packager.package(topic, script_or_research=script, style=style)
        record("packaging", packaging)

        if episode_id:
            # save_agent_output advances the episode status per stage, so by
            # here it already reads "assembling" — ready for an editor.
            ogx_db.log_decision(episode_id, "orchestrator", "pipeline_complete", {
                "style": style,
                "target_minutes": target_minutes,
                "researched": not skip_research,
            })

        console.print(Panel(
            "[bold green]OGX pipeline complete![/bold green]\n"
            "[dim]Outputs in outputs/ogx/ — thumbnail generation and title "
            "scoring still run through vidIQ.[/dim]",
            style="green",
        ))
        return {
            "topic": topic,
            "style": style,
            "episode_id": episode_id,
            "research": research,
            "script": script,
            "build_sheet": build_sheet,
            "packaging": packaging,
        }

    @staticmethod
    def _ogx_model() -> str:
        from config.settings import settings
        return settings.model

    # ------------------------------------------------------------------ #
    #  WORKFLOW 2: Financial Content Production Pipeline                   #
    # ------------------------------------------------------------------ #

    def produce_finance_video(self, topic: str) -> dict:
        """
        Full pipeline: Financial Analysis → Script → Social Media Bundle.

        Args:
            topic: The financial topic (e.g. "Bitcoin ETF Impact on Retail Investors")

        Returns: dict with analysis, script, and social_bundle
        """
        console.print(Panel(
            f"[bold]Finance Video Pipeline[/bold]\nTopic: {topic}",
            style="green",
        ))

        console.print("\n[bold][Step 1/3][/bold] Analyzing financial topic...")
        analysis = self.financial_agent.analyze_topic(topic)

        console.print("\n[bold][Step 2/3][/bold] Writing script...")
        script = self.script_finance.write_script(
            topic_or_research=analysis,
            target_minutes=15,
        )

        console.print("\n[bold][Step 3/3][/bold] Creating social media bundle...")
        social_bundle = self.marketing_agent.create_social_bundle(
            brand="finance_channel",
            topic=f"New financial analysis video: {topic}",
        )

        console.print(Panel("[bold green]Finance video pipeline complete![/bold green]", style="green"))
        return {
            "topic": topic,
            "analysis": analysis,
            "script": script,
            "social_bundle": social_bundle,
        }

    # ------------------------------------------------------------------ #
    #  WORKFLOW 3: Shopify Reporting (lazy import - needs API keys)        #
    # ------------------------------------------------------------------ #

    def weekly_shopify_report(self) -> str:
        """
        Generate a weekly Shopify sales performance report.
        Requires SHOPIFY_SHOP_NAME and SHOPIFY_ACCESS_TOKEN in .env
        """
        console.print(Panel("[bold]Weekly Shopify Report[/bold]", style="yellow"))
        from agents.shopify_reporting import ShopifyReportingAgent
        agent = ShopifyReportingAgent()
        return agent.generate_weekly_report()

    def monthly_shopify_report(self) -> str:
        """Generate a monthly Shopify sales performance report."""
        console.print(Panel("[bold]Monthly Shopify Report[/bold]", style="yellow"))
        from agents.shopify_reporting import ShopifyReportingAgent
        agent = ShopifyReportingAgent()
        return agent.generate_monthly_report()

    # ------------------------------------------------------------------ #
    #  WORKFLOW 4: Music Studio Lead Outreach                              #
    # ------------------------------------------------------------------ #

    def studio_outreach(self, prospect: dict) -> str:
        """
        Generate a complete cold outreach sequence for a music studio prospect.

        Args:
            prospect: dict with 'name', 'genre', 'followers', etc.

        Returns: Complete 4-email sequence as markdown
        """
        console.print(Panel(
            f"[bold]Studio Outreach[/bold]\nProspect: {prospect.get('name', 'Unknown')}",
            style="magenta",
        ))
        return self.lead_agent.create_studio_outreach(prospect)

    # ------------------------------------------------------------------ #
    #  WORKFLOW 5: YouTube Sponsorship Pitch                               #
    # ------------------------------------------------------------------ #

    def sponsorship_pitch(self, brand_info: dict, channel: str = "history_channel") -> str:
        """
        Generate a sponsorship pitch package for a potential sponsor.

        Args:
            brand_info: dict with 'name', 'industry', 'product'
            channel: 'history_channel' or 'finance_channel'

        Returns: Complete sponsorship package as markdown
        """
        console.print(Panel(
            f"[bold]Sponsorship Pitch[/bold]\nBrand: {brand_info.get('name', 'Unknown')}",
            style="cyan",
        ))
        return self.lead_agent.create_sponsorship_pitch(brand_info, channel=channel)

    # ------------------------------------------------------------------ #
    #  WORKFLOW 6b: Alpaca Paper Trading (lazy import - needs API keys)    #
    # ------------------------------------------------------------------ #

    def trading_overview(self) -> str:
        """Snapshot of the Alpaca paper account: equity, positions, orders."""
        console.print(Panel("[bold]Paper Trading Account Overview[/bold]", style="green"))
        from agents.trading_agent import TradingAgent
        return TradingAgent().account_overview()

    def trading_analyze(self, symbol: str) -> str:
        """Analyze a ticker and propose a paper trade (does not place orders)."""
        console.print(Panel(
            f"[bold]Trade Analysis[/bold]\nSymbol: {symbol.upper()}",
            style="green",
        ))
        from agents.trading_agent import TradingAgent
        return TradingAgent().analyze_symbol(symbol)

    def trading_execute(self, instruction: str) -> str:
        """Execute a natural-language trade instruction in the paper account."""
        console.print(Panel(
            f"[bold]Execute Paper Trade[/bold]\n{instruction}",
            style="green",
        ))
        from agents.trading_agent import TradingAgent
        return TradingAgent().execute_instruction(instruction)

    def run_auto_trader(
        self,
        symbols: list[str],
        interval_minutes: int = 15,
        cash_per_trade: float = 1000.0,
        max_positions: int = 5,
        budget: float = 5000.0,
        short_window: int = 20,
        long_window: int = 50,
        once: bool = False,
        enter_on_trend: bool = False,
        confirm_volume: bool = False,
        market_filter: bool = False,
        timeframe: str = "1Day",
        stop_loss_pct: float = 0.0,
        take_profit_pct: float = 0.0,
        trailing_stop_pct: float = 0.0,
        flatten_eod: bool = False,
        daily_loss_limit: float = 0.0,
        mode: str = "swing",
        strategy: str = "sma",
        or_bars: int = 6,
        dry_run: bool = False,
        llm_review: bool = False,
    ) -> None:
        """
        Run the deterministic SMA-crossover auto-trading loop (paper only).

        once=True runs a single decision cycle; otherwise loops every
        interval_minutes until interrupted. dry_run logs decisions without
        placing any orders. llm_review has Claude sanity-check each cycle's
        proposed trades (and veto risky ones) before execution.
        """
        mode = "single cycle" if once else f"every {interval_minutes} min"
        console.print(Panel(
            f"[bold]Auto-Trader (paper)[/bold]\n"
            f"Watchlist: {', '.join(s.upper() for s in symbols)}\n"
            f"Mode: {mode}{' · DRY-RUN' if dry_run else ''}",
            style="green",
        ))
        from agents.auto_trader import AutoTrader
        trader = AutoTrader(
            symbols=symbols,
            interval_minutes=interval_minutes,
            cash_per_trade=cash_per_trade,
            max_positions=max_positions,
            budget=budget,
            short_window=short_window,
            long_window=long_window,
            timeframe=timeframe,
            enter_on_trend=enter_on_trend,
            confirm_volume=confirm_volume,
            market_filter=market_filter,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            trailing_stop_pct=trailing_stop_pct,
            flatten_eod=flatten_eod,
            daily_loss_limit=daily_loss_limit,
            mode=mode,
            strategy=strategy,
            or_bars=or_bars,
            dry_run=dry_run,
            llm_review=llm_review,
        )
        if once:
            trader.run_once()
        else:
            trader.run_forever()

    # ------------------------------------------------------------------ #
    #  WORKFLOW 6: Content Calendar                                        #
    # ------------------------------------------------------------------ #

    def generate_content_calendar(self, weeks: int = 4) -> dict:
        """
        Generate video ideas for a multi-week content calendar.

        Args:
            weeks: Number of weeks to plan (default 4)

        Returns: dict with history_ideas and finance_ideas
        """
        console.print(Panel(f"[bold]{weeks}-Week Content Calendar[/bold]", style="white"))

        console.print("\n[bold][Step 1/2][/bold] Generating history channel ideas...")
        history_ideas = self.research_agent.run(
            f"Generate {weeks * 2} compelling YouTube video ideas for a historical "
            f"educational channel. For each: title, one-line hook, 3 key points, "
            f"search volume estimate (High/Medium/Low). Sort by potential."
        )

        console.print("\n[bold][Step 2/2][/bold] Generating finance channel ideas...")
        finance_ideas = self.financial_agent.generate_video_ideas(
            niche="personal finance and investing",
            count=weeks * 2,
        )

        return {
            "history_channel_ideas": history_ideas,
            "finance_channel_ideas": finance_ideas,
        }
