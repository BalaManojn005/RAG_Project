import { useEffect, useState } from "react";
import "./App.css";

import {
  uploadDocument,
  askQuestion,
  getConversations,
  getConversation,
  deleteConversation,
} from "./services/api";

function App() {
  const [file, setFile] = useState(null);

  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");

  const [conversationId, setConversationId] = useState(null);
  const [conversations, setConversations] = useState([]);

  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const [status, setStatus] = useState("");

  // ============================================================
  // LOAD ALL CONVERSATIONS
  // ============================================================

  const loadConversations = async () => {
    try {
      setLoadingHistory(true);

      const result = await getConversations();

      setConversations(result.conversations || []);
    } catch (error) {
      console.error("History loading error:", error);
    } finally {
      setLoadingHistory(false);
    }
  };

  // ============================================================
  // LOAD HISTORY WHEN APP STARTS
  // ============================================================

  useEffect(() => {
    loadConversations();
  }, []);

  // ============================================================
  // UPLOAD DOCUMENT
  // ============================================================

  const handleUpload = async () => {
    if (!file) {
      setStatus("Please choose a PDF first.");
      return;
    }

    try {
      setUploading(true);
      setStatus("Uploading and indexing document...");

      const result = await uploadDocument(file);

      setStatus(
        `✅ ${result.filename} indexed successfully.`
      );
    } catch (error) {
      console.error("Upload error:", error);

      setStatus("❌ Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  // ============================================================
  // NEW CHAT
  // ============================================================

  const handleNewChat = () => {
    setConversationId(null);
    setMessages([]);
    setQuestion("");
    setStatus("");
  };

  // ============================================================
  // OPEN CONVERSATION
  // ============================================================

  const handleOpenConversation = async (id) => {
    if (asking) {
      return;
    }

    try {
      setLoadingHistory(true);

      const conversation = await getConversation(id);

      setConversationId(conversation.id);

      setMessages(conversation.messages || []);

      setQuestion("");

      setStatus("");
    } catch (error) {
      console.error(
        "Conversation loading error:",
        error
      );

      setStatus("❌ Failed to load conversation.");
    } finally {
      setLoadingHistory(false);
    }
  };

  // ============================================================
  // DELETE CONVERSATION
  // ============================================================

  const handleDeleteConversation = async (id) => {
    if (asking) {
      return;
    }

    try {
      await deleteConversation(id);

      if (conversationId === id) {
        setConversationId(null);
        setMessages([]);
        setQuestion("");
        setStatus("");
      }

      await loadConversations();
    } catch (error) {
      console.error(
        "Delete conversation error:",
        error
      );

      setStatus("❌ Failed to delete conversation.");
    }
  };

  // ============================================================
  // ASK QUESTION
  // ============================================================

  const handleAsk = async () => {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || asking) {
      return;
    }

    // ----------------------------------------------------------
    // Add user message immediately
    // ----------------------------------------------------------

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: trimmedQuestion,
      },
    ]);

    setQuestion("");
    setAsking(true);

    try {
      // --------------------------------------------------------
      // Send question with current conversation ID
      // --------------------------------------------------------

      const result = await askQuestion(
        trimmedQuestion,
        conversationId
      );

      // --------------------------------------------------------
      // Save conversation ID
      // --------------------------------------------------------

      setConversationId(result.conversation_id);

      // --------------------------------------------------------
      // Add AI answer
      // --------------------------------------------------------

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: result.answer,
        },
      ]);

      // --------------------------------------------------------
      // Refresh history
      // --------------------------------------------------------

      await loadConversations();
    } catch (error) {
      console.error("Chat error:", error);

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content:
            "❌ Failed to get an answer from the AI.",
        },
      ]);
    } finally {
      setAsking(false);
    }
  };

  // ============================================================
  // UI
  // ============================================================

  return (
    <div className="app">

      {/* ======================================================
          HEADER
      ====================================================== */}

      <header className="header">
        <h1>AI Document Assistant</h1>

        <p>
          Upload a document and ask questions about it.
        </p>
      </header>

      {/* ======================================================
          MAIN
      ====================================================== */}

      <main className="container">

        {/* ====================================================
            HISTORY SIDEBAR
        ==================================================== */}

        <aside className="history-card">

          <div className="history-header">

            <h2>🕘 History</h2>

            <button
              onClick={handleNewChat}
              disabled={asking}
            >
              ＋ New Chat
            </button>

          </div>

          <div className="history-list">

            {loadingHistory &&
              conversations.length === 0 && (
                <div className="history-loading">
                  Loading history...
                </div>
              )}

            {!loadingHistory &&
              conversations.length === 0 && (
                <div className="history-empty">
                  No conversations yet.
                </div>
              )}

            {conversations.map((conversation) => (
              <div
                key={conversation.id}
                className={`history-item ${
                  conversationId === conversation.id
                    ? "active"
                    : ""
                }`}
              >

                {/* Open conversation */}

                <button
                  className="history-open"
                  onClick={() =>
                    handleOpenConversation(
                      conversation.id
                    )
                  }
                  disabled={
                    loadingHistory || asking
                  }
                >
                  <div className="history-title">
                    {conversation.title ||
                      "New Chat"}
                  </div>

                  <div className="history-date">
                    {conversation.updated_at
                      ? new Date(
                          conversation.updated_at
                        ).toLocaleString()
                      : ""}
                  </div>
                </button>

                {/* Delete conversation */}

                <button
                  className="history-delete"
                  onClick={() =>
                    handleDeleteConversation(
                      conversation.id
                    )
                  }
                  disabled={asking}
                  title="Delete conversation"
                >
                  🗑️
                </button>

              </div>
            ))}

          </div>
        </aside>

        {/* ====================================================
            MAIN CONTENT
        ==================================================== */}

        <section className="main-content">

          {/* ==================================================
              UPLOAD SECTION
          ================================================== */}

          <section className="upload-card">

            <h2>📄 Upload Document</h2>

            <div className="upload-box">

              <p>
                Choose a PDF document to analyze
              </p>

              <input
                type="file"
                accept=".pdf"
                onChange={(e) =>
                  setFile(e.target.files[0])
                }
              />

              {file && (
                <p>
                  Selected:{" "}
                  <strong>{file.name}</strong>
                </p>
              )}

              <button
                onClick={handleUpload}
                disabled={uploading}
              >
                {uploading
                  ? "Indexing..."
                  : "Upload & Index"}
              </button>

              {status && <p>{status}</p>}

            </div>
          </section>

          {/* ==================================================
              CHAT SECTION
          ================================================== */}

          <section className="chat-card">

            {/* Chat header */}

            <div className="chat-header">

              <div>
                <h2>💬 Ask Your Document</h2>

                {conversationId && (
                  <small>
                    Conversation active
                  </small>
                )}
              </div>

              <button
                onClick={handleNewChat}
                disabled={asking}
              >
                New Chat
              </button>

            </div>

            {/* =================================================
                CHAT WINDOW
            ================================================= */}

            <div className="chat-window">

              {messages.length === 0 && (
                <div className="empty-chat">
                  🤖 Ask a question about your document.
                </div>
              )}

              {messages.map((message, index) => (
                <div
                  key={`${message.timestamp || ""}-${index}`}
                  className={`message ${message.role}`}
                >

                  <div className="message-label">
                    {message.role === "user"
                      ? "👤 You"
                      : "🤖 AI"}
                  </div>

                  <div className="message-content">
                    {message.content}
                  </div>

                </div>
              ))}

              {/* =================================================
                  AI THINKING INDICATOR
              ================================================= */}

              {asking && (
                <div className="message assistant">

                  <div className="message-label">
                    🤖 AI
                  </div>

                  <div className="message-content thinking-content">

                    <span className="thinking-text">
                      Thinking
                    </span>

                    <span className="thinking-dots">

                      <span className="thinking-dot"></span>

                      <span className="thinking-dot"></span>

                      <span className="thinking-dot"></span>

                    </span>

                  </div>
                </div>
              )}

            </div>

            {/* =================================================
                QUESTION INPUT
            ================================================= */}

            <div className="question-box">

              <input
                type="text"
                placeholder="Ask something about your document..."
                value={question}
                onChange={(e) =>
                  setQuestion(e.target.value)
                }
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleAsk();
                  }
                }}
                disabled={asking}
              />

              <button
                onClick={handleAsk}
                disabled={asking}
              >
                {asking ? "..." : "Send"}
              </button>

            </div>

          </section>
        </section>
      </main>
    </div>
  );
}

export default App;