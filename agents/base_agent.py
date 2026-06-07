"""
BaseAgent: The foundation for every agent in the JoeMoyo system.

Implements the Claude tool-use agentic loop:
1. Send user message + tools to Claude
2. If Claude returns tool_use blocks, execute them
3. Feed tool results back to Claude
4. Repeat until Claude returns end_turn with a final text response

Hardened with patterns from the 12-factor-agents methodology:
- Factor 8 (own your control flow): the loop is bounded by max_tool_iterations
  so a misbehaving model can't trigger an infinite / runaway-cost loop, and
  every API stop_reason is handled explicitly.
- Factor 9 (compact errors into context): tool failures are caught and fed back
  to the model as structured error tool_results instead of crashing the run,
  giving the model a chance to recover or report the failure gracefully.
"""

import os
from abc import ABC, abstractmethod
from datetime import datetime

import anthropic
from rich.console import Console

from config.settings import settings

console = Console()


class BaseAgent(ABC):
    """Abstract base class all agents inherit from."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.model
        self.max_tokens = settings.max_tokens
        self.max_tool_iterations = settings.max_tool_iterations
        self.tool_definitions = self._define_tools()

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
        Automatically handles the full tool-use agentic loop.

        The loop is bounded by ``max_tool_iterations`` (Factor 8) and tool
        failures are fed back to the model rather than crashing the run
        (Factor 9).
        """
        messages = [{"role": "user", "content": user_message}]
        agent_name = self.__class__.__name__

        console.print(f"\n[bold blue][{agent_name}][/bold blue] Starting task...")

        for iteration in range(1, self.max_tool_iterations + 1):
            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "system": self.system_prompt,
                "messages": messages,
            }
            if self.tool_definitions:
                kwargs["tools"] = self.tool_definitions

            response = self.client.messages.create(**kwargs)

            # Claude finished, or wants to talk to the user, or hit the token
            # cap — any of these means we stop looping and return the text.
            if response.stop_reason in ("end_turn", "stop_sequence"):
                console.print(f"[bold green][{agent_name}][/bold green] Done.")
                return self._extract_text(response)

            if response.stop_reason == "max_tokens":
                console.print(
                    f"[bold red][{agent_name}][/bold red] Response hit max_tokens "
                    f"({self.max_tokens}); output may be truncated."
                )
                return self._extract_text(response)

            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            if not tool_use_blocks:
                # No tools requested and not a known terminal reason — return
                # whatever text we have rather than spinning.
                return self._extract_text(response)

            # Add Claude's response (with tool calls) to message history
            messages.append({"role": "assistant", "content": response.content})

            # Execute all requested tools and collect results (errors included)
            tool_results = []
            for tool_block in tool_use_blocks:
                console.print(f"  [yellow]-> Tool: {tool_block.name}[/yellow]")
                content, is_error = self._run_tool_safely(
                    tool_block.name, tool_block.input
                )
                result_block = {
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": content,
                }
                if is_error:
                    result_block["is_error"] = True
                tool_results.append(result_block)

            # Feed tool results back to Claude
            messages.append({"role": "user", "content": tool_results})

        # Loop budget exhausted (Factor 8): stop deterministically instead of
        # looping forever, and return the best text we have so far.
        console.print(
            f"[bold red][{agent_name}][/bold red] Reached max_tool_iterations "
            f"({self.max_tool_iterations}); stopping."
        )
        return self._extract_text(response) or (
            f"[{agent_name}] stopped after {self.max_tool_iterations} tool "
            f"iterations without producing a final answer."
        )

    def _run_tool_safely(self, tool_name: str, tool_input: dict) -> tuple[str, bool]:
        """
        Execute a tool and never raise (Factor 9: compact errors into context).

        Returns a ``(content, is_error)`` tuple. On failure the exception is
        turned into a compact, model-readable message so Claude can retry,
        choose another approach, or report the problem — rather than the whole
        agent run crashing on a transient tool error (timeout, 4xx/5xx, etc.).
        """
        try:
            return str(self._execute_tool(tool_name, tool_input)), False
        except Exception as exc:  # noqa: BLE001 - surfaced to the model, not swallowed
            error_message = (
                f"Tool '{tool_name}' failed with {type(exc).__name__}: {exc}. "
                f"Do not retry the exact same call repeatedly; adjust the input, "
                f"try a different approach, or continue without this tool."
            )
            console.print(f"  [red]Tool error ({tool_name}): {exc}[/red]")
            return error_message, True

    def _extract_text(self, response) -> str:
        """
        Concatenate all text blocks from a Claude API response.

        Returns every text block joined (not just the first) so responses that
        interleave text with tool calls or thinking aren't truncated.
        """
        parts = [block.text for block in response.content if hasattr(block, "text")]
        return "\n".join(parts).strip()

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
