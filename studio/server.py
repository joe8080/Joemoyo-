"""The studio as a connector (MCP server): `python -m studio.server`.

It plans, routes, guards the budget, remembers results and assembles. It does
not generate media itself: the assistant runs the generation connectors and
reports back here.
"""

import functools

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from studio import StudioError, api

server = MCPServer(
    "studio",
    instructions=(
        "Joe's personal video studio. Flow: studio_new plans a video from a script; "
        "studio_next lists jobs and the generation connector to use for each; write "
        "picture prompts with studio_prompts; get each tool's live price and record it "
        "with studio_quote; show Joe the totals from studio_status and, once he approves, "
        "set caps with studio_budget; call studio_start before every paid generation and "
        "only run the jobs it returns under 'started'; record links with studio_done; "
        "finish with studio_assemble. Follow each status result's next_step."
    ),
)


def tool(fn):
    """Register a studio tool; a StudioError reaches the assistant as a readable message."""
    @functools.wraps(fn)
    def run(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except StudioError as err:
            raise ToolError(str(err)) from None
    return server.tool()(run)


@tool
def studio_presets() -> dict:
    """List the house styles a video can be made in."""
    return api.presets()


@tool
def studio_routes(kind: str | None = None) -> dict:
    """Which generation connector gets each kind of job (voiceover, image, motion, music), best first."""
    return api.routes(kind)


@tool
def studio_new(title: str, preset: str, script: str) -> dict:
    """Plan a new video: split the script into voiceover scenes and picture shots. Spends nothing."""
    return api.new(title, preset, script)


@tool
def studio_projects() -> list[dict]:
    """List video projects and each one's next step."""
    return api.projects()


@tool
def studio_status(slug: str) -> dict:
    """Progress, credits spent against each cap, quotes still to come, and the next step."""
    return api.status(slug)


@tool
def studio_next(slug: str) -> dict:
    """Jobs ready to run (connector, tool, and exactly what to send), shots needing a prompt, and jobs waiting."""
    return api.next_jobs(slug)


@tool
def studio_prompts(slug: str, prompts: dict[str, str]) -> dict:
    """Set picture prompts as {shot id: prompt}. Describe the subject only; the house style is added automatically."""
    return api.set_prompts(slug, prompts)


@tool
def studio_quote(slug: str, credits: float, job_ids: list[str] | None = None,
                 kind: str | None = None) -> dict:
    """Record the live price per job, read from the generation tool's own estimate, for named jobs or a whole kind."""
    return api.quote(slug, credits, job_ids, kind)


@tool
def studio_budget(slug: str, caps: dict[str, float]) -> dict:
    """Set spending caps per wallet, in that tool's credits. Only with amounts Joe has approved."""
    return api.set_budget(slug, caps)


@tool
def studio_start(slug: str, job_ids: list[str]) -> dict:
    """The budget guard. Call before running paid generations; run only the jobs returned under 'started'."""
    return api.start(slug, job_ids)


@tool
def studio_done(slug: str, results: dict[str, str]) -> dict:
    """Record finished jobs as {job id: link or file path}."""
    return api.done(slug, results)


@tool
def studio_fail(slug: str, job_id: str, reason: str, refunded: bool = False) -> dict:
    """Mark a running job as failed. Set refunded when the tool returned the credits."""
    return api.fail(slug, job_id, reason, refunded)


@tool
def studio_reroute(slug: str, job_ids: list[str]) -> dict:
    """Move jobs to the next connector down their list. They need a fresh quote afterwards."""
    return api.reroute(slug, job_ids)


@tool
def studio_assemble(slug: str) -> dict:
    """Build the finished MP4 and caption file from the recorded results. Free."""
    return api.assemble(slug)


if __name__ == "__main__":
    server.run("stdio")
