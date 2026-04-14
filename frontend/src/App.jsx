import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const API_BASE = 'https://agri-support-agent-production.up.railway.app';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndref = useRef(null);
 

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    const userMessage = input.trim();
    setInput('');
    setIsLoading(true);
    setError(null);
    setMessages(prev => [
      ...prev, 
      {
        role: 'user', 
        content: userMessage, 
        timestamp: new Date().toISOString()
      }
    ]);

    try {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ message: userMessage })
  });

  const data = await response.json();

  setMessages(prev => [
    ...prev,
    {
      role: 'assistant',
      content: data.reply,
      timestamp: new Date().toISOString()
    }
  ]);

} catch (err) {
  console.error(err);
  setError("Failed to connect to server");
}

setIsLoading(false);
  };

  return (
    <div className="app">
      <div className="chat-container">
        <div className="chat-header">
          <div className="header-content">
            <h1>Agrochemical Support</h1>
            <p className="status">🟢 Ready</p>
          </div>
        </div>
        <div className="messages-area">
          {messages.length === 0 && (
            <div className="welcome-message">
              <h2>Welcome to Support</h2>
              <p>Ask us anything about our products, pricing, or usage guidelines.</p>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-content">{msg.content}</div>
            </div>
          ))}
          {isLoading && (
            <div className="message assistant">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        {error && (
          <div className="error-banner">
            {error}
            <button onClick={() => setError(null)}>✕</button>
          </div>
        )}
        <form onSubmit={handleSendMessage} className="input-form">
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Type your question..." disabled={isLoading} className="message-input" />
          <button type="submit" disabled={isLoading || !input.trim()} className="send-button">Send</button>
        </form>
      </div>
    </div>
  );
}
