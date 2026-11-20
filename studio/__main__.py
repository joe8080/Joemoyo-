"""Command line for the studio: `python -m studio <command>`. Every command prints JSON."""

import json
import sys
from pathlib import Path

import click

from studio import StudioError, api


def _show(result) -> None:
    click.echo(json.dumps(result, indent=2))


@click.group()
def cli():
    """Joe's personal studio. Projects live in outputs/studio (or $STUDIO_HOME)."""


@cli.command()
def presets():
    """List the house styles."""
    _show(api.presets())


@cli.command()
@click.argument("kind", required=False)
def routes(kind):
    """Show which tool gets each kind of job, best first."""
    _show(api.routes(kind))


@cli.command()
@click.option("--title", required=True)
@click.option("--preset", required=True)
@click.option("--script", "script_file", required=True, type=click.Path(exists=True, dir_okay=False))
def new(title, preset, script_file):
    """Plan a new video from a script file."""
    _show(api.new(title, preset, Path(script_file).read_text()))


@cli.command("list")
def list_projects():
    """List projects and each one's next step."""
    _show(api.projects())


@cli.command()
@click.argument("slug")
def status(slug):
    """Progress, spend against caps, and the next step."""
    _show(api.status(slug))


@cli.command("next")
@click.argument("slug")
def next_jobs(slug):
    """Jobs ready to run, with the tool to call and exactly what to send it."""
    _show(api.next_jobs(slug))


@cli.command()
@click.argument("slug")
@click.argument("source", type=click.File("r"))
def prompts(slug, source):
    """Set picture prompts from JSON {"shot id": "prompt"}. Use - to read stdin."""
    _show(api.set_prompts(slug, json.load(source)))


@cli.command()
@click.argument("slug")
@click.argument("credits", type=float)
@click.argument("job_ids", nargs=-1)
@click.option("--kind", help="Price every open paid job of this kind instead of naming jobs.")
def quote(slug, credits, job_ids, kind):
    """Record the live price (per job) for the named jobs or a whole kind."""
    _show(api.quote(slug, credits, list(job_ids), kind))


@cli.command()
@click.argument("slug")
@click.argument("caps", nargs=-1, required=True)
def budget(slug, caps):
    """Set spending caps Joe approved, e.g. openart=120 elevenlabs=9000."""
    try:
        parsed = {wallet: float(cap) for wallet, cap in (c.split("=", 1) for c in caps)}
    except ValueError:
        raise StudioError("Write each cap as wallet=number, for example openart=120.") from None
    _show(api.set_budget(slug, parsed))


@cli.command()
@click.argument("slug")
@click.argument("job_ids", nargs=-1, required=True)
def start(slug, job_ids):
    """The budget guard: call before running paid tools. Stops at the first refusal."""
    _show(api.start(slug, list(job_ids)))


@cli.command()
@click.argument("slug")
@click.argument("results", nargs=-1, required=True)
def done(slug, results):
    """Record results as job=link-or-file-path, one or many."""
    pairs = [r.split("=", 1) for r in results]
    if any(len(pair) != 2 for pair in pairs):
        raise StudioError("Write each result as job=link, for example music=https://...")
    _show(api.done(slug, dict(pairs)))


@cli.command()
@click.argument("slug")
@click.argument("job_id")
@click.argument("reason")
@click.option("--refunded", is_flag=True, help="The tool gave the credits back.")
def fail(slug, job_id, reason, refunded):
    """Mark a running job as failed."""
    _show(api.fail(slug, job_id, reason, refunded))


@cli.command()
@click.argument("slug")
@click.argument("job_ids", nargs=-1, required=True)
def reroute(slug, job_ids):
    """Move jobs to the next tool down their list."""
    _show(api.reroute(slug, list(job_ids)))


@cli.command()
@click.argument("slug")
def assemble(slug):
    """Build the finished MP4 and caption file. Free; runs locally."""
    _show(api.assemble(slug))


def main() -> None:
    try:
        cli(standalone_mode=False)
    except StudioError as err:
        _show({"error": str(err)})
        sys.exit(1)
    except click.ClickException as err:
        _show({"error": err.format_message()})
        sys.exit(2)
    except click.exceptions.Abort:
        sys.exit(130)


if __name__ == "__main__":
    main()
