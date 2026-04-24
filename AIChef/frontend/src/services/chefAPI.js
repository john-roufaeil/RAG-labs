import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chefAPI = {
  // Check health
  health: async () => {
    const response = await api.get('/health');
    return response.data;
  },

  // Chat with chef
  chat: async (sessionId, message, creativity = 'balanced', verbosity = 'normal') => {
    const response = await api.post('/chat', {
      session_id: sessionId,
      message,
      creativity,
      verbosity,
    });
    return response.data;
  },

  // Set chef personality
  setPersonality: async (sessionId, creativity, verbosity) => {
    const response = await api.post('/set-personality', {
      session_id: sessionId,
      creativity,
      verbosity,
    });
    return response.data;
  },

  // Get session state
  getSessionState: async (sessionId) => {
    const response = await api.get(`/session/${sessionId}`);
    return response.data;
  },

  // Reset session
  resetSession: async (sessionId) => {
    const response = await api.post(`/reset/${sessionId}`);
    return response.data;
  },
};

export default api;
