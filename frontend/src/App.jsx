import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const API_BASE = 'https://agri-support-agent-production.up.railway.app';

export default function App() {
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const initConversation = async () => {
      try {
        const customerId = `user_${Math.random().toString(36).substr(2, 9)}`;
        const response = await fetch(`${API_BASE}/api/conversations?customer_id=${customerId}&channel=web`, {
          method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to create conversation');
        const data = await response.json();
        setConversationId(data.conversation_id);
        setError(null);
      } catch (err) {
        setError('Failed to initialize chat. Please refresh.');
        console.error(err);
      }
    };
    initConversation();
  }, []);

  useEffect(() => {
    if (!conversationId) return;
    const connectWebSocket = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `wss://agri-support-agent-production.up.railway.app/ws/chat/${conversationId}`;
      const ws = new WebSocket(wsUrl);
      ws.onopen = () => {
        setConnected(true);
        console.log('WebSocket connected');
      };
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'message') {
          setMessages(prev => [...prev, {role: data.role, content: data.content, timestamp: data.timestamp}]);
          setIsLoading(false);
        } else if (data.type === 'error') {
          setError(data.content);
          setIsLoading(false);
        }
      };
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Connection error. Please refresh.');
        setConnected(false);
      };
      ws.onclose = () => {
        setConnected(false);
        setTimeout(connectWebSocket, 3000);
      };
 

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
            <p className="status">{error ? '🔴 error' : '🟢 Ready'}</p>
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
          <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Type your question..." disabled={!connected || isLoading} className="message-input" />
          <button type="submit" disabled={!connected || isLoading || !input.trim()} className="send-button">Send</button>
        </form>
      </div>
    </div>
  );
}
