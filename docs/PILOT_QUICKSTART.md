# Pilot local CLI quickstart

Requires Python 3.10+ and this full checked-out development repository; **the SKILL.md alone is not a self-contained runtime**. These examples create `.handoffs` in the selected repository. Decide what may be committed before sharing.

```bash
python scripts/handoff.py --repo . init
python scripts/handoff.py --repo . write --payload examples/session_payload.json
python scripts/handoff.py --repo . list
python scripts/handoff.py --repo . resume latest
python scripts/handoff.py --repo . doctor
# Replace SESSION_ID with the id returned by write:
python scripts/handoff.py --repo . archive SESSION_ID --confirm
python scripts/handoff.py --repo . list --archived
python scripts/handoff.py --repo . restore SESSION_ID --confirm
# Updating an existing record requires a current revision:
python scripts/handoff.py --repo . write --payload examples/session_payload.json --id SESSION_ID --expected-revision 1
```

All outputs are JSON except errors on stderr. A write is **not a conversation export**: populate the payload explicitly from the agent and independently check its claims. `resume` is a read-only data comparison; it never runs commands. Lock or interrupted transitions: run `doctor`, inspect and back up affected files before manual repair.
