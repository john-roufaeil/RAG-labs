import React, { useState } from 'react';
import '../styles/ChatInput.css';

export const ChatInput = ({ onSendMessage, loading, disabled }) => {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim() && !loading && !disabled) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-input">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Tell the chef what you'd like to cook..."
        disabled={loading || disabled}
        className="input-field"
        rows="3"
      />
      <button
        onClick={handleSend}
        disabled={loading || disabled || !input.trim()}
        className="send-button"
      >
        {loading ? '⏳ Waiting...' : '📤 Send'}
      </button>
    </div>
  );
};

export default ChatInput;
