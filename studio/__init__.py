"""Joe's personal studio: presets, routing, planning, budget guard and assembly.

The engine never calls a paid generator itself. Claude runs the connected tools
(Higgsfield, ElevenLabs, OpenArt, Artlist); the engine decides which tool gets
each job, refuses spend past the cap, remembers results, and builds the MP4.
"""


class StudioError(Exception):
    """A problem the person driving the studio can fix; the message says how."""


class BudgetError(StudioError):
    """A paid job was refused by the budget guard."""
