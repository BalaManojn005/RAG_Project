import { useEffect, useState } from "react";
import "./App.css";

import {
  uploadDocument,
  streamQuestion,
  getConversations,
  getConversation,
  deleteConversation,
} from "./services/api";


function App() {
  const [file, setFile] = useState(null);

  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");

  const [conversationId, setConversationId] =
    useState(null);

  const [conversations, setConversations] =
    useState([]);

  const [uploading, setUploading] =
    useState(false);

  const [asking, setAsking] =
    useState(false);

  const [loadingHistory, setLoadingHistory] =
    useState(false);

  const [status, setStatus] =
    useState("");


  // ============================================================
  // LOAD ALL CONVERSATIONS
  // ============================================================

  const loadConversations = async () => {
    try {
      setLoadingHistory(true);

      const result =
        await getConversations();

      setConversations(
        result.conversations || []
      );

    } catch (error) {
      console.error(
        "History loading error:",
        error
      );
    } finally {
      setLoadingHistory(false);
    }
  };


  // ============================================================
  // LOAD HISTORY WHEN APP STARTS
  // ============================================================

  useEffect(() => {
    const timer =
      window.setTimeout(() => {
        void loadConversations();
      }, 0);

    return () =>
      window.clearTimeout(timer);
  }, []);


  // ============================================================
  // UPLOAD DOCUMENT
  // ============================================================

  const handleUpload = async () => {
    if (!file) {
      setStatus(
        "Please choose a PDF first."
      );
      return;
    }

    try {
      setUploading(true);

      setStatus(
        "Uploading and indexing document..."
      );

      const result =
        await uploadDocument(file);

      setStatus(
        `✅ ${result.filename} indexed successfully.`
      );

    } catch (error) {
      console.error(
        "Upload error:",
        error
      );

      setStatus(
        `❌ ${
          error.message ||
          "Upload failed."
        }`
      );

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

  const handleOpenConversation =
    async (id) => {

      if (asking) {
        return;
      }

      try {
        setLoadingHistory(true);

        const conversation =
          await getConversation(id);

        setConversationId(
          conversation.id
        );

        setMessages(
          conversation.messages || []
        );

        setQuestion("");
        setStatus("");

      } catch (error) {
        console.error(
          "Conversation loading error:",
          error
        );

        setStatus(
          "❌ Failed to load conversation."
        );

      } finally {
        setLoadingHistory(false);
      }
    };


  // ============================================================
  // DELETE CONVERSATION
  // ============================================================

  const handleDeleteConversation =
    async (id) => {

      if (asking) {
        return;
      }

      try {
        setLoadingHistory(true);

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

        setStatus(
          "❌ Failed to delete conversation."
        );

      } finally {
        setLoadingHistory(false);
      }
    };


  // ============================================================
  // ASK QUESTION — TRUE STREAMING
  // ============================================================

  const handleAsk = async () => {
    const trimmedQuestion =
      question.trim();

    if (
      !trimmedQuestion ||
      asking
    ) {
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
        timestamp:
          new Date().toISOString(),
      },
    ]);


    // ----------------------------------------------------------
    // Create empty assistant message
    // ----------------------------------------------------------

    setMessages((previous) => [
      ...previous,
      {
        role: "assistant",
        content: "",
        sources: [],
        streaming: true,
        timestamp:
          new Date().toISOString(),
      },
    ]);


    setQuestion("");
    setAsking(true);
    setStatus("");


    try {

      await streamQuestion(
        trimmedQuestion,
        conversationId,
        {

          // ====================================================
          // CONVERSATION ID
          // ====================================================

          onConversation: (id) => {
            setConversationId(id);
          },


          // ====================================================
          // TOKEN
          // ====================================================

          onToken: (token) => {

            setMessages((previous) => {

              const updated = [
                ...previous,
              ];

              const lastIndex =
                updated.length - 1;

              if (
                updated[lastIndex]?.role ===
                "assistant"
              ) {

                updated[lastIndex] = {
                  ...updated[lastIndex],

                  content:
                    (
                      updated[lastIndex]
                        .content || ""
                    ) + token,
                };
              }

              return updated;
            });
          },


          // ====================================================
          // SOURCES
          // ====================================================

          onSources: (sources) => {

            setMessages((previous) => {

              const updated = [
                ...previous,
              ];

              const lastIndex =
                updated.length - 1;

              if (
                updated[lastIndex]?.role ===
                "assistant"
              ) {

                updated[lastIndex] = {
                  ...updated[lastIndex],

                  sources:
                    sources || [],
                };
              }

              return updated;
            });
          },


          // ====================================================
          // STREAM COMPLETE
          // ====================================================

          onDone: (id) => {

            if (id) {
              setConversationId(id);
            }


            setMessages((previous) => {

              const updated = [
                ...previous,
              ];

              const lastIndex =
                updated.length - 1;

              if (
                updated[lastIndex]?.role ===
                "assistant"
              ) {

                updated[lastIndex] = {
                  ...updated[lastIndex],

                  streaming: false,
                };
              }

              return updated;
            });
          },


          // ====================================================
          // STREAM ERROR
          // ====================================================

          onError: (message) => {

            throw new Error(
              message ||
              "Streaming failed."
            );
          },
        }
      );


      // --------------------------------------------------------
      // Refresh history
      // --------------------------------------------------------

      await loadConversations();

    } catch (error) {

      console.error(
        "Streaming chat error:",
        error
      );


      setMessages((previous) => {

        const updated = [
          ...previous,
        ];

        const lastIndex =
          updated.length - 1;

        if (
          updated[lastIndex]?.role ===
          "assistant"
        ) {

          updated[lastIndex] = {
            ...updated[lastIndex],

            content:
              `❌ ${
                error.message ||
                "Failed to get an answer from the AI."
              }`,

            streaming: false,
          };
        }

        return updated;
      });

    } finally {
      setAsking(false);
    }
  };


  // ============================================================
  // ENTER KEY
  // ============================================================

  const handleKeyDown = (event) => {

    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {

      event.preventDefault();

      handleAsk();
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

        <h1>
          AI Document Assistant
        </h1>

        <p>
          Upload a document and ask
          questions about it.
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

            <h2>
              🕘 History
            </h2>

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


            {conversations.map(
              (conversation) => (

                <div
                  key={conversation.id}
                  className={
                    `history-item ${
                      conversationId ===
                      conversation.id
                        ? "active"
                        : ""
                    }`
                  }
                >

                  {/* Open */}

                  <button
                    className="history-open"
                    onClick={() =>
                      handleOpenConversation(
                        conversation.id
                      )
                    }
                    disabled={
                      loadingHistory ||
                      asking
                    }
                  >

                    <div className="history-title">

                      {
                        conversation.title ||
                        "New Chat"
                      }

                    </div>


                    <div className="history-date">

                      {
                        conversation.updated_at
                          ? new Date(
                              conversation.updated_at
                            ).toLocaleString()
                          : ""
                      }

                    </div>

                  </button>


                  {/* Delete */}

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
              )
            )}

          </div>

        </aside>


        {/* ====================================================
            MAIN CONTENT
        ==================================================== */}

        <section className="main-content">


          {/* ==================================================
              UPLOAD
          ================================================== */}

          <section className="upload-card">

            <h2>
              📄 Upload Document
            </h2>


            <div className="upload-box">

              <p>
                Choose a PDF document
                to analyze
              </p>


              <input
                type="file"
                accept=".pdf"
                onChange={(event) => {

                  setFile(
                    event.target.files?.[0] ||
                    null
                  );

                }}
              />


              {file && (
                <p>
                  Selected:{" "}
                  <strong>
                    {file.name}
                  </strong>
                </p>
              )}


              <button
                onClick={handleUpload}
                disabled={uploading}
              >

                {
                  uploading
                    ? "Indexing..."
                    : "Upload & Index"
                }

              </button>


              {status && (
                <p>
                  {status}
                </p>
              )}

            </div>

          </section>


          {/* ==================================================
              CHAT
          ================================================== */}

          <section className="chat-card">


            {/* Chat Header */}

            <div className="chat-header">

              <div>

                <h2>
                  💬 Ask Your Document
                </h2>

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

                  🤖 Ask a question
                  about your document.

                </div>
              )}


              {messages.map(
                (message, index) => (

                  <div
                    key={
                      `${message.timestamp || ""}-${index}`
                    }
                    className={
                      `message ${message.role}`
                    }
                  >

                    <div className="message-label">

                      {
                        message.role ===
                        "user"
                          ? "👤 You"
                          : "🤖 AI"
                      }

                    </div>


                    <div className="message-content">

                      {message.content}

                      {/* Streaming cursor */}

                      {message.streaming && (
                        <span className="streaming-cursor">
                          ▋
                        </span>
                      )}

                    </div>


                    {/* =================================================
                        SOURCES
                    ================================================= */}

                    {
                      message.role ===
                        "assistant" &&
                      message.sources?.length >
                        0 && (

                        <details className="sources">

                          <summary>
                            📚 Sources (
                            {
                              message.sources.length
                            }
                            )
                          </summary>


                          <div className="sources-list">

                            {
                              message.sources.map(
                                (
                                  source,
                                  sourceIndex
                                ) => (

                                  <div
                                    key={
                                      sourceIndex
                                    }
                                    className="source-item"
                                  >

                                    <div>
                                      <strong>
                                        Source{" "}
                                        {
                                          source.rank ||
                                          sourceIndex +
                                            1
                                        }
                                      </strong>
                                    </div>


                                    {
                                      source.chunk_id !==
                                        undefined && (
                                        <div>
                                          Chunk:{" "}
                                          {
                                            source.chunk_id
                                          }
                                        </div>
                                      )
                                    }


                                    {source.score !==
                                      undefined &&
                                      source.score !==
                                        null && (
                                        <div>
                                          Score:{" "}
                                          {
                                            Number(
                                              source.score
                                            ).toFixed(
                                              4
                                            )
                                          }
                                        </div>
                                      )}


                                    {source.content && (
                                      <p>
                                        {
                                          source.content
                                        }
                                      </p>
                                    )}

                                  </div>
                                )
                              )
                            }

                          </div>

                        </details>
                      )
                    }

                  </div>
                )
              )}


              {/* Thinking indicator */}

              {asking &&
                messages[
                  messages.length - 1
                ]?.role !==
                  "assistant" && (

                  <div className="message assistant">

                    <div className="message-label">
                      🤖 AI
                    </div>

                    <div className="message-content thinking-content">

                      <span>
                        Thinking
                      </span>

                      <span className="thinking-dots">

                        <span className="thinking-dot">
                        </span>

                        <span className="thinking-dot">
                        </span>

                        <span className="thinking-dot">
                        </span>

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
                placeholder={
                  "Ask something about your document..."
                }
                value={question}
                onChange={(event) =>
                  setQuestion(
                    event.target.value
                  )
                }
                onKeyDown={handleKeyDown}
                disabled={asking}
              />


              <button
                onClick={handleAsk}
                disabled={
                  asking ||
                  !question.trim()
                }
              >

                {
                  asking
                    ? "Generating..."
                    : "Send"
                }

              </button>

            </div>

          </section>

        </section>

      </main>

    </div>
  );
}


export default App;