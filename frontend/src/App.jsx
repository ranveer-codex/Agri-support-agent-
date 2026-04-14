import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const API_BASE = 'https://agri-support-agent-production.up.railway.app';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const [isReady, setIsReady] = useState(false);

  const messagesEndRef = useRef(null);

  // 🔹 Initialize conversation
  useEffect(() => {
    const initConversation = async () => {
      try {
        const customerId = `user_${Math.random().toString(36).substring(2, 9)}`;

        const response = await fetch(
          `${API_BASE}/api/conversations?customer_id=${customerId}`,
          { method: "POST" }
        );

        const data = await response.json();

        if (!response.ok || !data.conversation_id) {
          throw new Error("Failed to create conversation");
        }

        setConversationId(data.conversation_id);
        setIsReady(true);

      } catch (err) {
        console.error("Init error:", err);
        setError("Failed to initialize chat. Please refresh.");
      }
    };

    initConversation();
  }, []);

  // 🔹 Auto scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 🔹 Send message
  const handleSendMessage = async (e) => {
    e.preventDefault();

    if (!input.trim() || isLoading || !conversationId) return;

    const userMessage = input.trim();

    setMessages(prev => [
      ...prev,
      { role: 'user', content: userMessage }
    ]);

    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          message: userMessage,
          conversation_id: conversationId
        })
      });

      const data = await response.json();
      console.log("API RESPONSE:", data);

      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: data.reply || "No response from server"
        }
      ]);

    } catch (err) {
      console.error("Chat error:", err);
      setError("Failed to connect to server");
    }

    setIsLoading(false);
  };

  return (
    <div className="app">
      <div className="chat-container">

        {/* 🔹 Header */}
        <div className="chat-header">
          <div className="header-content">
            <h1>Agrochemical Support</h1>
            <p className="status">
              {isReady ? "🟢 Ready" : "🟡 Connecting..."}
            </p>
          </div>
        </div>

        {/* 🔹 Messages */}
        <div className="messages-area">
          {messages.length === 0 && (
            <div className="welcome-message">
              <h2>Welcome to Support</h2>
              <p>Ask us anything about our products.</p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-content">{msg.content}</div>
            </div>
          ))}

          {isLoading && (
            <div className="message assistant">
              <div className="message-content">Typing...</div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 🔹 Error */}
        {error && (
          <div className="error-banner">
            {error}
            <button onClick={() => setError(null)}>✕</button>
          </div>
        )}

        {/* 🔹 Input */}
        <form onSubmit={handleSendMessage} className="input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your question..."
            disabled={!isReady || isLoading}
          />
          <button
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
