from collections import defaultdict

from app.config import MAX_HISTORY_TURNS

# ponytail: in-memory only, lost on restart - fine for a local demo. Swap for
# a real store (redis/db) if the project ever needs to survive a server restart.
_sessions: dict[str, list[dict]] = defaultdict(list)


def get_history(session_id: str) -> list[dict]:
    return _sessions[session_id]


def add_turn(session_id: str, user_message: str, model_message: str) -> None:
    history = _sessions[session_id]
    history.append({"role": "user", "text": user_message})
    history.append({"role": "model", "text": model_message})
    del history[: max(0, len(history) - MAX_HISTORY_TURNS * 2)]
