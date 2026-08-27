import json
import os
import uuid
from datetime import datetime


# ============================================================
# STORAGE PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

HISTORY_DIR = os.path.join(
    BASE_DIR,
    "data",
    "history"
)

HISTORY_FILE = os.path.join(
    HISTORY_DIR,
    "conversations.json"
)


# ============================================================
# STORAGE HELPERS
# ============================================================

def _ensure_storage():
    os.makedirs(
        HISTORY_DIR,
        exist_ok=True
    )

    if not os.path.exists(HISTORY_FILE):
        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                {},
                file,
                ensure_ascii=False,
                indent=2
            )


def _load_history():
    _ensure_storage()

    try:
        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            history = json.load(file)

    except (
        json.JSONDecodeError,
        OSError
    ):
        return {}

    # --------------------------------------------------------
    # Current project format = dictionary
    # --------------------------------------------------------

    if isinstance(history, dict):
        return history

    # --------------------------------------------------------
    # Safety migration if an old list exists
    # --------------------------------------------------------

    if isinstance(history, list):

        converted = {}

        for conversation in history:

            if not isinstance(
                conversation,
                dict
            ):
                continue

            conversation_id = conversation.get(
                "id"
            )

            if conversation_id:
                converted[
                    conversation_id
                ] = conversation

        return converted

    return {}


def _save_history(history):
    _ensure_storage()

    temporary_file = (
        HISTORY_FILE + ".tmp"
    )

    with open(
        temporary_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            history,
            file,
            ensure_ascii=False,
            indent=2
        )

    os.replace(
        temporary_file,
        HISTORY_FILE
    )


# ============================================================
# CREATE CONVERSATION
# ============================================================

def create_conversation(
    title="New Chat"
):
    history = _load_history()

    now = datetime.now().isoformat()

    conversation_id = str(
        uuid.uuid4()
    )

    conversation = {
        "id": conversation_id,
        "title": title,
        "created_at": now,
        "updated_at": now,
        "messages": []
    }

    history[conversation_id] = conversation

    _save_history(history)

    return conversation


# ============================================================
# GET CONVERSATION
# ============================================================

def get_conversation(
    conversation_id
):
    history = _load_history()

    conversation = history.get(
        conversation_id
    )

    if conversation is None:
        return None

    return conversation


# ============================================================
# GET ALL CONVERSATIONS
# ============================================================

def get_all_conversations():
    history = _load_history()

    conversations = list(
        history.values()
    )

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
    content,
    sources=None
):
    history = _load_history()

    conversation = history.get(
        conversation_id
    )

    if conversation is None:
        return None

    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }

    # --------------------------------------------------------
    # Persist sources for assistant messages
    # --------------------------------------------------------

    if role == "assistant":
        message["sources"] = (
            sources or []
        )

    conversation.setdefault(
        "messages",
        []
    ).append(message)

    conversation["updated_at"] = (
        datetime.now().isoformat()
    )

    # --------------------------------------------------------
    # Automatically create title from
    # first user question
    # --------------------------------------------------------

    if (
        role == "user"
        and (
            not conversation.get("title")
            or conversation.get("title")
            == "New Chat"
        )
    ):

        title = content.strip()

        if len(title) > 60:
            title = (
                title[:57]
                + "..."
            )

        conversation["title"] = title

    history[conversation_id] = conversation

    _save_history(history)

    return conversation


# ============================================================
# DELETE CONVERSATION
# ============================================================

def delete_conversation(
    conversation_id
):
    history = _load_history()

    if conversation_id not in history:
        return False

    del history[
        conversation_id
    ]

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