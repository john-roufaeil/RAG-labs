import React, { useState, useEffect } from 'react';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import Sidebar from './components/Sidebar';
import { chefAPI } from './services/chefAPI';
import './styles/App.css';

function App() {
  // State management
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [creativity, setCreativity] = useState('balanced');
  const [verbosity, setVerbosity] = useState('normal');
  const [sessionId] = useState(`user_${Date.now()}`);
  const [ingredients, setIngredients] = useState([]);
  const [currentStage, setCurrentStage] = useState('greeting');
  const [error, setError] = useState(null);

  // Handle personality changes
  useEffect(() => {
    if (messages.length > 0) {
      handlePersonalityChange();
    }
  }, [creativity, verbosity]);

  const handlePersonalityChange = async () => {
    try {
      await chefAPI.setPersonality(sessionId, creativity, verbosity);
    } catch (err) {
      console.error('Error setting personality:', err);
    }
  };

  const handleSendMessage = async (userMessage) => {
    if (!userMessage.trim()) return;

    // Add user message to chat
    const userMsg = {
      role: 'user',
      content: userMessage,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setError(null);

    try {
      // Call chef API
      const response = await chefAPI.chat(
        sessionId,
        userMessage,
        creativity,
        verbosity
      );

      // Add chef response to chat
      const chefMsg = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, chefMsg]);

      // Update state from response
      setCurrentStage(response.current_stage);
      setIngredients(response.collected_ingredients);
    } catch (err) {
      const errorMsg = {
        role: 'error',
        content: `Error: ${err.message || 'Failed to get response from chef'}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    try {
      await chefAPI.resetSession(sessionId);
      setMessages([]);
      setIngredients([]);
      setCurrentStage('greeting');
      setError(null);
    } catch (err) {
      console.error('Error resetting session:', err);
      setError('Failed to reset session');
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>👨‍🍳 AI Chef Assistant</h1>
        <p>Your personal cooking guide powered by AI</p>
      </header>

      <div className="app-container">
        <div className="main-content">
          <ChatWindow messages={messages} loading={loading} />
          <ChatInput
            onSendMessage={handleSendMessage}
            loading={loading}
            disabled={error !== null}
          />
          {error && (
            <div className="error-banner">
              ⚠️ {error}
            </div>
          )}
        </div>

        <Sidebar
          creativity={creativity}
          setCreativity={setCreativity}
          verbosity={verbosity}
          setVerbosity={setVerbosity}
          sessionId={sessionId}
          ingredients={ingredients}
          currentStage={currentStage}
          onReset={handleReset}
        />
      </div>
    </div>
  );
}

export default App;
