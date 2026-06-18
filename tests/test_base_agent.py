"""
Behavioral tests for the hardened BaseAgent agentic loop.

These run with NO real API calls — the Anthropic SDK and the model responses
are stubbed — so they're fast and safe to run anywhere (no API key needed
beyond a dummy value to satisfy settings import).

Run directly:        python tests/test_base_agent.py
Or with pytest:      pytest tests/test_base_agent.py

They lock in the 12-factor patterns added to BaseAgent:
  - Factor 8 (own your control flow): the loop is bounded by max_tool_iterations.
  - Factor 9 (compact errors into context): tool failures are fed back to the
    model as error tool_results instead of crashing the run.
"""

import os
import sys
import types

# --- Make the repo importable and stub external deps BEFORE importing app code ---
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-real")  # satisfy settings
os.environ["MAX_TOOL_ITERATIONS"] = "3"

# Stub the anthropic SDK so no network call / client init happens.
_fake_anthropic = types.ModuleType("anthropic")
_fake_anthropic.Anthropic = lambda *a, **k: None
sys.modules["anthropic"] = _fake_anthropic

from agents.base_agent import BaseAgent  # noqa: E402


# --- Minimal fakes mimicking the Anthropic message API shape ---
class Block:
    def __init__(self, type, **kw):
        self.type = type
        for k, v in kw.items():
            setattr(self, k, v)


class Resp:
    def __init__(self, stop_reason, content):
        self.stop_reason = stop_reason
        self.content = content


class ScriptedMessages:
    """Returns queued responses; repeats the last one once exhausted."""

    def __init__(self, script):
        self.script = script
        self.calls = 0

    def create(self, **kwargs):
        resp = self.script[min(self.calls, len(self.script) - 1)]
        self.calls += 1
        return resp


class DummyAgent(BaseAgent):
    @property
    def system_prompt(self):
        return "test"

    def _define_tools(self):
        return [{"name": "boom"}]

    def _execute_tool(self, name, inp):
        if name == "boom":
            raise RuntimeError("simulated network 401")
        return "tool ok"


def _agent_with(script):
    agent = DummyAgent()
    agent.client = types.SimpleNamespace(messages=ScriptedMessages(script))
    return agent


def test_tool_error_is_fed_back_not_raised():
    """Factor 9: a raising tool must not crash the run; model recovers."""
    agent = _agent_with([
        Resp("tool_use", [Block("tool_use", name="boom", input={}, id="t1")]),
        Resp("end_turn", [Block("text", text="Recovered without the tool.")]),
    ])
    out = agent.run("do it")
    assert "Recovered" in out


def test_loop_is_bounded_by_max_iterations():
    """Factor 8: endless tool-calling stops at max_tool_iterations (=3)."""
    agent = _agent_with([
        Resp("tool_use", [Block("tool_use", name="ok", input={}, id="t1")]),
    ])
    agent.run("loop")
    assert agent.client.messages.calls == 3


def test_max_tokens_returns_partial_without_crash():
    agent = _agent_with([Resp("max_tokens", [Block("text", text="partial...")])])
    assert agent.run("x") == "partial..."


def test_text_blocks_are_joined():
    """Factor 3: all text blocks are returned, not just the first."""
    agent = _agent_with([
        Resp("end_turn", [Block("text", text="part one"), Block("text", text="part two")]),
    ])
    assert agent.run("x") == "part one\npart two"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS: {t.__name__}")
    print(f"\nAll {len(tests)} tests passed.")
