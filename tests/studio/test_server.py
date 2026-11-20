"""The same engine offered as a connector. Talks to the real server over stdio."""

import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters, stdio_client

SCRIPT = "The harbour burned for six days.\n\n" + " ".join(["stone"] * 60) + "."


def talk(tmp_path, conversation):
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "studio.server"],
        env={**os.environ, "STUDIO_HOME": str(tmp_path)})

    async def main():
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await conversation(session)

    return asyncio.run(main())


def payload(result):
    return json.loads(result.content[0].text)


def test_the_connector_offers_the_studio_tools(tmp_path):
    async def conversation(session):
        return [tool.name for tool in (await session.list_tools()).tools]

    names = talk(tmp_path, conversation)
    assert {"studio_new", "studio_next", "studio_quote", "studio_start",
            "studio_done", "studio_assemble"} <= set(names)


def test_a_project_can_be_planned_through_the_connector(tmp_path):
    async def conversation(session):
        return await session.call_tool(
            "studio_new", {"title": "Carthage", "preset": "history", "script": SCRIPT})

    out = payload(talk(tmp_path, conversation))
    assert (out["slug"], out["shots"]) == ("carthage", 4)


def test_the_budget_guard_refuses_through_the_connector_too(tmp_path):
    async def conversation(session):
        await session.call_tool(
            "studio_new", {"title": "Carthage", "preset": "history", "script": SCRIPT})
        return await session.call_tool(
            "studio_start", {"slug": "carthage", "job_ids": ["vo-s01"]})

    out = payload(talk(tmp_path, conversation))
    assert out["started"] == [] and "quote" in out["refused"]["why"]


def test_a_mistake_comes_back_as_a_tool_error(tmp_path):
    async def conversation(session):
        return await session.call_tool("studio_status", {"slug": "nope"})

    result = talk(tmp_path, conversation)
    assert result.is_error and "no projects yet" in result.content[0].text
