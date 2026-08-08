import { useState } from "react";
import "./App.css";
import { uploadDocument, askQuestion } from "./services/api";

function App() {
  const [file, setFile] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");

  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [status, setStatus] = useState("");

  const handleUpload = async () => {
    if (!file) {
      setStatus("Please choose a PDF first.");
      return;
    }

    try {
      setUploading(true);
      setStatus("Uploading and indexing document...");

      const result = await uploadDocument(file);

      setStatus(`✅ ${result.filename} indexed successfully.`);
    } catch (error) {
      console.error(error);
      setStatus("❌ Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const handleAsk = async () => {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || asking) {
      return;
    }

    // Add user message immediately
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
      const result = await askQuestion(trimmedQuestion);

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: result.answer,
        },
      ]);
    } catch (error) {
      console.error(error);

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: "❌ Failed to get an answer from the AI.",
        },
      ]);
    } finally {
      setAsking(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>AI Document Assistant</h1>
        <p>Upload a document and ask questions about it.</p>
      </header>

      <main className="container">

        {/* Upload Section */}
        <section className="upload-card">
          <h2>📄 Upload Document</h2>

          <div className="upload-box">
            <p>Choose a PDF document to analyze</p>

            <input
              type="file"
              accept=".pdf"
              onChange={(e) => setFile(e.target.files[0])}
            />

            {file && (
              <p>
                Selected: <strong>{file.name}</strong>
              </p>
            )}

            <button
              onClick={handleUpload}
              disabled={uploading}
            >
              {uploading ? "Indexing..." : "Upload & Index"}
            </button>

            {status && <p>{status}</p>}
          </div>
        </section>

        {/* Chat Section */}
        <section className="chat-card">
          <h2>💬 Ask Your Document</h2>

          <div className="chat-window">

            {messages.length === 0 && (
              <div className="empty-chat">
                🤖 Ask a question about your document.
              </div>
            )}

            {messages.map((message, index) => (
              <div
                key={index}
                className={`message ${message.role}`}
              >
                <div className="message-label">
                  {message.role === "user" ? "👤 You" : "🤖 AI"}
                </div>

                <div className="message-content">
                  {message.content}
                </div>
              </div>
            ))}

            {asking && (
              <div className="message assistant">
                <div className="message-label">🤖 AI</div>
                <div className="message-content">
                  Thinking...
                </div>
              </div>
            )}

          </div>

          <div className="question-box">
            <input
              type="text"
              placeholder="Ask something about your document..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleAsk();
                }
              }}
            />

            <button
              onClick={handleAsk}
              disabled={asking}
            >
              {asking ? "..." : "Send"}
            </button>
          </div>
        </section>

      </main>
    </div>
  );
}

export default App;