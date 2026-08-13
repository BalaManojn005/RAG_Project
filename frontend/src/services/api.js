const API_URL = "http://127.0.0.1:8001";

// ============================================================
// UPLOAD DOCUMENT
// ============================================================

export async function uploadDocument(file) {
  const formData = new FormData();

  formData.append("file", file);

  const response = await fetch(`${API_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Failed to upload document");
  }

  return response.json();
}


// ============================================================
// ASK QUESTION
// ============================================================

export async function askQuestion(
  question,
  conversationId = null
) {
  const body = {
    question,
  };

  // Add conversation ID when continuing
  // an existing conversation.
  if (conversationId) {
    body.conversation_id = conversationId;
  }

  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error("Failed to get AI response");
  }

  return response.json();
}


// ============================================================
// GET CONVERSATION
// ============================================================

export async function getConversation(conversationId) {
  const response = await fetch(
    `${API_URL}/history/${conversationId}`
  );

  if (!response.ok) {
    throw new Error("Failed to load conversation");
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
    throw new Error("Failed to load conversation history");
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
    throw new Error("Failed to delete conversation");
  }

  return response.json();
}