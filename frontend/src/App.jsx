import React, { useState, useEffect, useRef } from "react";
import "./App.css";

const API_BASE = "https://agri-support-agent-production.up.railway.app";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState(null);

  const messagesEndRef = useRef(null);

  // 🔹 Init conversation
  useEffect(() => {
    const initConversation = async () => {
      try {
        const customerId = `user_${Math.random().toString(36).substring(2, 9)}`;

        const res = await fetch(
          `${API_BASE}/api/conversations?customer_id=${customerId}`,
          { method: "POST" }
        );

        const data = await res.json();

        if (!res.ok || !data.conversation_id) {
          throw new Error("Failed to initialize");
        }

        setConversationId(data.conversation_id);
        setIsReady(true);
      } catch (err) {
        console.error(err);
        setError("Failed to connect to backend.");
      }
    };

    initConversation();
  }, []);

  // 🔹 Auto scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 🔹 Send message
  const handleSendMessage = async (e) => {
    e.preventDefault();

    if (!input.trim() || isLoading || !conversationId) return;

    const userMessage = input.trim();

    setMessages((prev) => [
      ...prev,
      { role: "user", content: userMessage }
    ]);

    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          message: userMessage,
          conversation_id: conversationId
        })
      });

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.reply || "No response",
          recommendations: data.recommendations || []
        }
      ]);
    } catch (err) {
      console.error(err);
      setError("Server connection failed.");
    }

    setIsLoading(false);
  };

  return (
    <div className="app">
      <div className="chat-container">

        {/* 🔹 HEADER */}
        <div className="chat-header">
          <div className="header-content">
            <h1>🌱 Agro Advisory System</h1>
            <p className="status">
              {isReady ? "🟢 Ready" : "🟡 Connecting..."}
            </p>
          </div>
        </div>

        {/* 🔹 MESSAGES */}
        <div className="messages-area">
          {messages.length === 0 && (
            <div className="welcome-message">
              <h2>Smart Crop Assistance</h2>
              <p>Ask about pests, diseases, fertilizers, or crop issues.</p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-content">
                {msg.content}

                {/* 🔥 PRODUCT CARDS */}
                {msg.recommendations?.length > 0 && (
                  <div className="product-list">
                    {msg.recommendations.map((p, i) => (
                      <div key={i} className="product-card">
                        <h4>{p.name}</h4>
                        {p.usage && <p><b>Usage:</b> {p.usage}</p>}
                        {p.target && <p><b>Target:</b> {p.target}</p>}
                        <button className="dealer-btn">
                          Contact Dealer
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="message assistant">
              <div className="message-content typing">
                Typing...
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 🔹 ERROR */}
        {error && (
          <div className="error-banner">
            {error}
            <button onClick={() => setError(null)}>✕</button>
          </div>
        )}

        {/* 🔹 INPUT */}
        <form onSubmit={handleSendMessage} className="input-form">
          <input
            className="message-input"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe your crop issue..."
            disabled={!isReady || isLoading}
          />
          <button
            className="send-button"
            type="submit"
            disabled={!isReady || isLoading || !input.trim()}
          >
            Send
          </button>
        </form>

      </div>
    </div>
  );
}
