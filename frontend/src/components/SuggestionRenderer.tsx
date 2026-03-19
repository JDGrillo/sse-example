import React, { useState, useEffect } from 'react';
import type { Correction } from '../types/corrections';
import './SuggestionRenderer.css';

interface SuggestionRendererProps {
  suggestions: Correction[];
  onAccept: (suggestion: Correction, index: number) => void;
  onReject: (index: number) => void;
  onAcceptAll?: () => void;
  onRejectAll?: () => void;
}

export const SuggestionRenderer: React.FC<SuggestionRendererProps> = ({
  suggestions,
  onAccept,
  onReject,
  onAcceptAll,
  onRejectAll,
}) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [newSuggestions, setNewSuggestions] = useState<Set<number>>(new Set());

  // Track when new suggestions arrive for animation
  useEffect(() => {
    if (suggestions.length > 0) {
      const indices = new Set(suggestions.map((_, idx) => idx));
      setNewSuggestions(indices);
      
      // Clear animation state after animations complete
      const timer = setTimeout(() => {
        setNewSuggestions(new Set());
      }, suggestions.length * 100 + 800);
      
      return () => clearTimeout(timer);
    }
  }, [suggestions.length]);

  if (suggestions.length === 0) {
    return null;
  }

  const toggleExpanded = (index: number) => {
    setExpandedIndex(expandedIndex === index ? null : index);
  };

  const getDisplayTypeColor = (type: Correction['type']) => {
    const colorMap = {
      grammar: '#e74c3c',
      spelling: '#e67e22',
      style: '#3498db',
      tone: '#9b59b6',
      rephrasing: '#27ae60',
    };
    return colorMap[type] || '#95a5a6';
  };

  const getDisplayTypeIcon = (type: Correction['type']) => {
    const iconMap = {
      grammar: 'G',
      spelling: 'S',
      style: 'ST',
      tone: 'T',
      rephrasing: 'R',
    };
    return iconMap[type] || '•';
  };

  return (
    <div className="suggestion-renderer">
      <div className="suggestion-header">
        <h3>
          Suggestions ({suggestions.length})
        </h3>
        {suggestions.length > 1 && (
          <div className="bulk-actions">
            {onAcceptAll && (
              <button
                className="bulk-action-btn accept-all"
                onClick={onAcceptAll}
                title="Accept all suggestions"
              >
                Accept All
              </button>
            )}
            {onRejectAll && (
              <button
                className="bulk-action-btn reject-all"
                onClick={onRejectAll}
                title="Reject all suggestions"
              >
                Reject All
              </button>
            )}
          </div>
        )}
      </div>

      <div className="suggestions-list">
        {suggestions.map((suggestion, index) => {
          const isNew = newSuggestions.has(index);
          return (
            <div
              key={index}
              className={`suggestion-item ${expandedIndex === index ? 'expanded' : ''} ${isNew ? 'suggestion-item-appear' : ''}`}
              style={isNew ? { animationDelay: `${index * 100}ms` } : undefined}
            >
              <div className="suggestion-type-indicator">
                <span 
                  className="type-badge"
                  style={{ backgroundColor: getDisplayTypeColor(suggestion.type) }}
                >
                  {getDisplayTypeIcon(suggestion.type)} {suggestion.type}
                </span>
            </div>

            <div className="suggestion-content">
              <div className="text-comparison">
                <div className="original-text">
                  <span className="label">Original:</span>
                  <span className="text strikethrough">{suggestion.original_text}</span>
                </div>
                <div className="arrow">→</div>
                <div className="suggested-text">
                  <span className="label">Suggested:</span>
                  <span className="text">{suggestion.suggested_text}</span>
                </div>
              </div>

              {suggestion.explanation && (
                <div 
                  className="explanation"
                  style={{ display: expandedIndex === index ? 'block' : 'none' }}
                >
                  <span className="label">Explanation:</span>
                  <p>{suggestion.explanation}</p>
                </div>
              )}

              {suggestion.explanation && (
                <button
                  className="toggle-explanation"
                  onClick={() => toggleExpanded(index)}
                >
                  {expandedIndex === index ? 'Hide' : 'Show'} explanation
                </button>
              )}
            </div>

            <div className="suggestion-actions">
              <button
                className="action-btn accept"
                onClick={() => onAccept(suggestion, index)}
                title="Accept this suggestion"
              >
                Accept
              </button>
              <button
                className="action-btn reject"
                onClick={() => onReject(index)}
                title="Reject this suggestion"
              >
                Reject
              </button>
            </div>
          </div>
        );
        })}
      </div>
    </div>
  );
};

export default SuggestionRenderer;
