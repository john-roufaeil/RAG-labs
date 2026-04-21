import React from 'react';
import '../styles/ChatWindow.css';

export const ChatWindow = ({ messages, loading }) => {
  const messagesEndRef = React.useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="chat-window">
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h2>👨‍🍳 Welcome to AI Chef</h2>
            <p>Start by greeting the chef and telling them what ingredients you have!</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`message message-${msg.role}`}
            >
              <div className="message-avatar">
                {msg.role === 'user' ? '👤' : '👨‍🍳'}
              </div>
              <div className="message-content">
                <p className="message-text">{msg.content}</p>
                <span className="message-time">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="message message-assistant">
            <div className="message-avatar">👨‍🍳</div>
            <div className="message-content">
              <div className="loading-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatWindow;
