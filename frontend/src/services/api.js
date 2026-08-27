const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8001";


// ============================================================
// ERROR HANDLER
// ============================================================

async function getErrorMessage(response, fallback) {
  try {
    const payload = await response.json();

    return (
      payload.detail ||
      payload.error ||
      fallback
    );
  } catch {
    return fallback;
  }
}


// ============================================================
// UPLOAD DOCUMENT
// ============================================================

export async function uploadDocument(file) {
  const formData = new FormData();

  formData.append("file", file);

  const response = await fetch(
    `${API_URL}/upload`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to upload document"
      )
    );
  }

  return response.json();
}


// ============================================================
// NORMAL CHAT
// ============================================================

export async function askQuestion(
  question,
  conversationId = null
) {
  const body = {
    question,
  };

  if (conversationId) {
    body.conversation_id = conversationId;
  }

  const response = await fetch(
    `${API_URL}/chat`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    }
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to get AI response"
      )
    );
  }

  return response.json();
}


// ============================================================
// STREAMING CHAT
// ============================================================

export async function streamQuestion(
  question,
  conversationId = null,
  callbacks = {}
) {
  const {
    onConversation,
    onToken,
    onSources,
    onDone,
    onError,
  } = callbacks;

  const body = {
    question,
  };

  if (conversationId) {
    body.conversation_id = conversationId;
  }

  const response = await fetch(
    `${API_URL}/chat/stream`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify(body),
    }
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to stream AI response"
      )
    );
  }

  if (!response.body) {
    throw new Error(
      "Streaming is not supported by this browser."
    );
  }

  const reader =
    response.body.getReader();

  const decoder =
    new TextDecoder("utf-8");

  let buffer = "";

  try {
    while (true) {
      const {
        value,
        done,
      } = await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(
        value,
        {
          stream: true,
        }
      );

      const events =
        buffer.split("\n\n");

      buffer =
        events.pop() || "";

      for (const event of events) {
        processSSEEvent(
          event,
          {
            onConversation,
            onToken,
            onSources,
            onDone,
            onError,
          }
        );
      }
    }

    if (buffer.trim()) {
      processSSEEvent(
        buffer,
        {
          onConversation,
          onToken,
          onSources,
          onDone,
          onError,
        }
      );
    }
  } finally {
    reader.releaseLock();
  }
}


// ============================================================
// SSE EVENT PROCESSOR
// ============================================================

function processSSEEvent(
  event,
  callbacks
) {
  if (!event.trim()) {
    return;
  }

  const lines =
    event.split("\n");

  let eventType = "message";
  let data = "";

  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventType =
        line.slice(6).trim();
    }

    if (line.startsWith("data:")) {
      data +=
        line.slice(5).trim();
    }
  }

  if (!data) {
    return;
  }

  let payload;

  try {
    payload = JSON.parse(data);
  } catch {
    return;
  }

  switch (eventType) {
    case "conversation":
      callbacks.onConversation?.(
        payload.conversation_id
      );
      break;

    case "token":
      callbacks.onToken?.(
        payload.content || ""
      );
      break;

    case "sources":
      callbacks.onSources?.(
        payload.sources || []
      );
      break;

    case "done":
      callbacks.onDone?.(
        payload.conversation_id
      );
      break;

    case "error":
      callbacks.onError?.(
        payload.message ||
        "Streaming error"
      );
      break;

    default:
      break;
  }
}


// ============================================================
// GET SINGLE CONVERSATION
// ============================================================

export async function getConversation(
  conversationId
) {
  const response = await fetch(
    `${API_URL}/history/${conversationId}`
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to load conversation"
      )
    );
  }

  return response.json();
}


// ============================================================
// GET ALL CONVERSATIONS
// ============================================================

export async function getConversations() {
  const response = await fetch(
    `${API_URL}/history`
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to load conversation history"
      )
    );
  }

  return response.json();
}


// ============================================================
// DELETE CONVERSATION
// ============================================================

export async function deleteConversation(
  conversationId
) {
  const response = await fetch(
    `${API_URL}/history/${conversationId}`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        "Failed to delete conversation"
      )
    );
  }

  return response.json();
}