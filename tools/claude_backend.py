"""
Claude Code CLI backend — run agents without an ANTHROPIC_API_KEY.

The default backend calls the Anthropic API directly through the `anthropic`
SDK, which needs a billed API key. This backend shells out to the Claude Code
CLI in headless mode (`claude -p`) instead, which authenticates with the
Claude Code session you are already signed into. Same models, no separate key,
no separate bill.

    AGENT_BACKEND=claude_cli python main.py ogx --topic "Queen Nzinga"

What changes when you switch backends
-------------------------------------
The SDK backend drives a tool-use loop over the Python tools each agent defines
(`_define_tools` / `_execute_tool`). The CLI backend cannot: `claude -p` brings
its own tools, and there is no way to hand it a Python callable. So in CLI mode
an agent's tools come from Claude Code instead —

    Python tool            CLI equivalent
    ---------------------  ------------------------------------------
    web_search (Brave)     WebSearch / WebFetch (built into Claude Code)
    ogx_db.* (PostgREST)   mcp__Supabase__execute_sql (the Supabase MCP)

Agents that need this declare `_cli_allowed_tools()` and, where the mechanism
differs enough to matter, `_cli_tool_appendix()` — a block appended to the task
prompt explaining how to reach the same data through the CLI's tools. The
system prompt, the evidence rules, and the output contract are unchanged, so
the deliverable is the same either way.

Requirements: the `claude` CLI on PATH and an authenticated Claude Code session.
For MCP-backed tools, point CLAUDE_MCP_CONFIG at an MCP config JSON.
"""

import os
import shutil
import subprocess

from dotenv import load_dotenv

load_dotenv()

# Long enough for a research pass with a dozen database round-trips.
DEFAULT_TIMEOUT = int(os.environ.get("CLAUDE_CLI_TIMEOUT", "1800"))
MCP_CONFIG = os.environ.get("CLAUDE_MCP_CONFIG", "")


class ClaudeBackendError(RuntimeError):
    """Raised when the CLI is missing, times out, or exits non-zero."""


def available() -> bool:
    return shutil.which("claude") is not None


def mcp_configured() -> bool:
    return bool(MCP_CONFIG and os.path.exists(MCP_CONFIG))


def require_available() -> None:
    if not available():
        raise EnvironmentError(
            "AGENT_BACKEND=claude_cli needs the Claude Code CLI on PATH.\n"
            "Install it from https://claude.com/claude-code, or unset "
            "AGENT_BACKEND to use the API-key backend instead."
        )


def run_prompt(
    system_prompt: str,
    user_prompt: str,
    model: str = "",
    allowed_tools: tuple[str, ...] = (),
    mcp_config: str = "",
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """
    Run one prompt through `claude -p` and return the final text.

    The agent's system prompt is APPENDED to Claude Code's own rather than
    replacing it (`--append-system-prompt`, not `--system-prompt`): replacing it
    strips the instructions that make the CLI's tools work, and a research agent
    that cannot drive its tools is worse than one carrying some extra harness
    text it ignores.
    """
    require_available()

    cmd = ["claude", "-p", "--append-system-prompt", system_prompt]
    if model:
        cmd += ["--model", model]

    config = mcp_config or MCP_CONFIG
    if config:
        if not os.path.exists(config):
            raise ClaudeBackendError(f"MCP config not found: {config}")
        cmd += ["--mcp-config", config]

    if allowed_tools:
        cmd += ["--allowedTools", *allowed_tools]

    try:
        # The prompt goes in on stdin so a long dossier can never hit ARG_MAX.
        result = subprocess.run(
            cmd, input=user_prompt, capture_output=True,
            text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        raise ClaudeBackendError(
            f"claude CLI timed out after {timeout}s. Raise CLAUDE_CLI_TIMEOUT "
            "for long research passes."
        ) from e

    if result.returncode != 0:
        raise ClaudeBackendError(
            f"claude CLI exited {result.returncode}: "
            f"{(result.stderr or result.stdout or '').strip()[:400]}"
        )

    output = (result.stdout or "").strip()
    if not output:
        raise ClaudeBackendError("claude CLI returned no output")
    return output
