import json
import uuid
from datetime import datetime
from pathlib import Path


# ============================================================
# HISTORY STORAGE
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

HISTORY_DIR = PROJECT_ROOT / "data" / "history"
HISTORY_FILE = HISTORY_DIR / "conversations.json"


# ============================================================
# INITIALIZE STORAGE
# ============================================================

def _ensure_storage():
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text(
            json.dumps({}, indent=2),
            encoding="utf-8"
        )


# ============================================================
# LOAD ALL CONVERSATIONS
# ============================================================

def _load_history():
    _ensure_storage()

    try:
        return json.loads(
            HISTORY_FILE.read_text(
                encoding="utf-8"
            )
        )
    except (json.JSONDecodeError, OSError):
        return {}


# ============================================================
# SAVE ALL CONVERSATIONS
# ============================================================

def _save_history(history):
    _ensure_storage()

    HISTORY_FILE.write_text(
        json.dumps(
            history,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


# ============================================================
# CREATE CONVERSATION
# ============================================================

def create_conversation(title="New Chat"):
    history = _load_history()

    conversation_id = str(uuid.uuid4())

    now = datetime.now().isoformat()

    history[conversation_id] = {
        "id": conversation_id,
        "title": title,
        "created_at": now,
        "updated_at": now,
        "messages": []
    }

    _save_history(history)

    return history[conversation_id]


# ============================================================
# GET CONVERSATION
# ============================================================

def get_conversation(conversation_id):
    history = _load_history()

    return history.get(conversation_id)


# ============================================================
# GET ALL CONVERSATIONS
# ============================================================

def get_all_conversations():
    history = _load_history()

    conversations = list(history.values())

    conversations.sort(
        key=lambda item: item.get(
            "updated_at",
            ""
        ),
        reverse=True
    )

    return conversations


# ============================================================
# ADD MESSAGE
# ============================================================

def add_message(
    conversation_id,
    role,
    content
):
    history = _load_history()

    if conversation_id not in history:
        return None

    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }

    history[conversation_id]["messages"].append(
        message
    )

    history[conversation_id]["updated_at"] = (
        datetime.now().isoformat()
    )

    # Automatically use the first user question
    # as the conversation title.
    if (
        role == "user"
        and history[conversation_id]["title"] == "New Chat"
    ):
        title = content.strip()

        if len(title) > 60:
            title = title[:57] + "..."

        history[conversation_id]["title"] = title

    _save_history(history)

    return message


# ============================================================
# DELETE CONVERSATION
# ============================================================

def delete_conversation(conversation_id):
    history = _load_history()

    if conversation_id not in history:
        return False

    del history[conversation_id]

    _save_history(history)

    return True


# ============================================================
# GET RECENT MESSAGES
# ============================================================

def get_recent_messages(
    conversation_id,
    limit=10
):
    conversation = get_conversation(
        conversation_id
    )

    if not conversation:
        return []

    messages = conversation.get(
        "messages",
        []
    )

    return messages[-limit:]