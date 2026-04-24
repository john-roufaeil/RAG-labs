import React from 'react';
import '../styles/Sidebar.css';

export const Sidebar = ({
  creativity,
  setCreativity,
  verbosity,
  setVerbosity,
  sessionId,
  ingredients,
  currentStage,
  onReset,
}) => {
  return (
    <div className="sidebar">
      <div className="sidebar-section">
        <h3>👨‍🍳 Chef Settings</h3>
        
        <div className="setting">
          <label>Creativity Level</label>
          <select value={creativity} onChange={(e) => setCreativity(e.target.value)}>
            <option value="strict">🏛️ Strict (Traditional)</option>
            <option value="balanced">⚖️ Balanced</option>
            <option value="creative">🎨 Creative</option>
          </select>
        </div>

        <div className="setting">
          <label>Verbosity</label>
          <select value={verbosity} onChange={(e) => setVerbosity(e.target.value)}>
            <option value="concise">📝 Concise</option>
            <option value="normal">💬 Normal</option>
            <option value="detailed">📚 Detailed</option>
          </select>
        </div>
      </div>

      <div className="sidebar-section">
        <h3>📊 Session Info</h3>
        <div className="info-item">
          <span>Session ID:</span>
          <code>{sessionId}</code>
        </div>
        <div className="info-item">
          <span>Stage:</span>
          <span className="stage-badge">{currentStage}</span>
        </div>
        <div className="info-item">
          <span>Ingredients:</span>
          <span className="ingredient-count">{ingredients.length}</span>
        </div>
      </div>

      {ingredients.length > 0 && (
        <div className="sidebar-section">
          <h3>🥬 Collected Ingredients</h3>
          <div className="ingredients-list">
            {ingredients.map((ing, idx) => (
              <span key={idx} className="ingredient-tag">
                {ing}
              </span>
            ))}
          </div>
        </div>
      )}

      <button onClick={onReset} className="reset-button">
        🔄 Reset Session
      </button>
    </div>
  );
};

export default Sidebar;
