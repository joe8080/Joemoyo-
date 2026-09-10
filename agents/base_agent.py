"""
BaseAgent: The foundation for every agent in the JoeMoyo system.

Implements the Claude tool-use agentic loop:
1. Send user message + tools to Claude
2. If Claude returns tool_use blocks, execute them
3. Feed tool results back to Claude
4. Repeat until Claude returns end_turn with a final text response
"""

import os
from abc import ABC, abstractmethod
from datetime import datetime

import anthropic
from rich.console import Console

from config.settings import settings
from agent_os import client as agent_os

console = Console()


class BaseAgent(ABC):
    """Abstract base class all agents inherit from."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.model
        self.max_tokens = settings.max_tokens
        self.tool_definitions = self._define_tools()
        # Board identity — shows up on Agent OS under this id (see agent_os/roster.py).
        if not getattr(self, "agent_id", None):
            self.agent_id = agent_os.slug_for(self.__class__.__name__)

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Each agent defines its own system prompt."""
        pass

    @abstractmethod
    def _define_tools(self) -> list:
        """Each agent declares which tools it needs. Return [] if no tools."""
        pass

    @abstractmethod
    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool call requested by Claude. Return the result as a string."""
        pass

    def run(self, user_message: str) -> str:
        """
        Run the agent with a user message.
        Automatically handles the full tool-use agentic loop and reports
        running / done / error to the Agent OS board.
        """
        agent_name = self.__class__.__name__
        agent_os.report(self.agent_id, "running", task=user_message)
        try:
            final_text = self._run_loop(user_message, agent_name)
        except Exception as e:
            agent_os.report(self.agent_id, "error", note=f"{type(e).__name__}: {e}", run_type=self.agent_id)
            raise
        agent_os.report(self.agent_id, "done", result=final_text, run_type=self.agent_id)
        return final_text

    def _run_loop(self, user_message: str, agent_name: str) -> str:
        messages = [{"role": "user", "content": user_message}]

        console.print(f"\n[bold blue][{agent_name}][/bold blue] Starting task...")

        while True:
            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "system": self.system_prompt,
                "messages": messages,
            }
            if self.tool_definitions:
                kwargs["tools"] = self.tool_definitions

            response = self.client.messages.create(**kwargs)

            # If Claude is done, extract and return the final text
            if response.stop_reason == "end_turn":
                final_text = self._extract_text(response)
                console.print(f"[bold green][{agent_name}][/bold green] Done.")
                return final_text

            # Process tool calls
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            if not tool_use_blocks:
                return self._extract_text(response)

            # Add Claude's response (with tool calls) to message history
            messages.append({"role": "assistant", "content": response.content})

            # Execute all requested tools and collect results
            tool_results = []
            for tool_block in tool_use_blocks:
                console.print(f"  [yellow]-> Tool: {tool_block.name}[/yellow]")
                agent_os.report(self.agent_id, "running", task=f"{user_message[:80]} · using {tool_block.name}", log_run=False)
                result = self._execute_tool(tool_block.name, tool_block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": str(result),
                })

            # Feed tool results back to Claude
            messages.append({"role": "user", "content": tool_results})

    def _extract_text(self, response) -> str:
        """Extract text content from a Claude API response."""
        for block in response.content:
            if hasattr(block, "text"):
                return block.text
        return ""

    def save_output(self, content: str, subdirectory: str, filename: str) -> str:
        """Save agent output to the outputs directory. Returns the saved file path."""
        output_path = os.path.join(settings.output_dir, subdirectory)
        os.makedirs(output_path, exist_ok=True)
        filepath = os.path.join(output_path, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        console.print(f"  [dim]Saved → {filepath}[/dim]")
        return filepath

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")
