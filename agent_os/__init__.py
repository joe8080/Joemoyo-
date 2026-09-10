"""
Agent OS — the board where every agent is visible, and the socket new agents
plug into. The control plane lives in Supabase (the Chief's `agent-os` edge
function: roster, task queue, approvals, events, per-agent keys). This package
is the JoeMoyo side of it:

    roster.py    the repo's agents as OS roster entries (key, supervisor, role)
    client.py    what an agent calls: report(), is_paused(), tasks, events
    worker.py    the runner: pulls tasks for the built-in agents and executes
    runners.py   what each built-in agent does when it gets a task
    board.html   the OS board, served as the gateway's front page
    edge/        the extended gateway source (deployed to Supabase)

    python main.py os connect   register the built-ins, issue their keys (once)
    python main.py os worker    run the built-ins as OS workers
    python main.py os status    the fleet, in the terminal
"""
