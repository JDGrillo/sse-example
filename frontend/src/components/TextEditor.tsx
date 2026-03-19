import React, { useState, useRef, useCallback, useEffect } from 'react';
import streamingAPIClient from '../services/streamingClient';
import { useDebounce } from '../hooks/useDebounce';
import type { StreamChunk, Correction } from '../types/corrections';
import './TextEditor.css';

interface TextEditorProps {
  text: string;
  onTextChange: (text: string) => void;
  onSuggestionsReceived?: (suggestions: Correction[]) => void;
  suggestions?: Correction[];
  onAcceptSuggestion?: (suggestion: Correction, index: number) => void;
  onRejectSuggestion?: (index: number) => void;
}

export const TextEditor: React.FC<TextEditorProps> = ({ 
  text,
  onTextChange, 
  onSuggestionsReceived,
  suggestions = [],
  onAcceptSuggestion,
  onRejectSuggestion
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isPreparing, setIsPreparing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [streamChunks, setStreamChunks] = useState<StreamChunk[]>([]);
  const [streamingContent, setStreamingContent] = useState<string>('');
  const [expandedSuggestionIndex, setExpandedSuggestionIndex] = useState<number | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState<{ top: number; left: number } | null>(null);
  const [newSuggestionIndices, setNewSuggestionIndices] = useState<Set<number>>(new Set());
  const abortControllerRef = useRef<AbortController | null>(null);
  const requestIdRef = useRef(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);

  /**
   * Send correction request to backend
   */
  const requestCorrections = useCallback(async (inputText: string) => {
    if (!inputText.trim()) {
      setStreamChunks([]);
      setIsPreparing(false);
      return;
    }

    // Cancel previous request if exists
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      console.log('🚫 Cancelled previous request - user is still typing');
    }

    setIsPreparing(false);
    setIsLoading(true);
    setError(null);
    setStreamChunks([]);
    setStreamingContent('');
    setNewSuggestionIndices(new Set());

    const currentRequestId = ++requestIdRef.current;

    try {
      // This returns immediately without blocking
      const controller = await streamingAPIClient.streamCorrections(
        {
          text: inputText,
          request_id: `req-${currentRequestId}`,
        },
        {
          onChunk: (chunk: StreamChunk) => {
            console.log('Received chunk:', chunk);
            
            // Update chunks array immediately for visual feedback
            setStreamChunks((prev) => [...prev, chunk]);

            // For streaming chunks, we could show partial content
            // but since we need complete JSON, we wait for 'complete' event
            if (chunk.type === 'chunk' && chunk.content) {
              // Accumulate streaming content for visual feedback
              setStreamingContent((prev) => prev + chunk.content);
            }

            // If chunk contains parsed corrections, notify parent
            if (chunk.type === 'complete' && chunk.content) {
              try {
                console.log('Full content received:', chunk.content);
                
                // Parse the JSON response from GPT-4o
                const parsed = JSON.parse(chunk.content);
                console.log('Parsed response:', parsed);
                
                // Extract corrections array from the response
                const corrections: Correction[] = parsed.corrections || [];
                console.log('Extracted corrections:', corrections);
                
                // Mark all suggestions as new for staggered animation
                const newIndices = new Set(corrections.map((_, idx) => idx));
                setNewSuggestionIndices(newIndices);
                
                // Clear animation state after all animations complete
                setTimeout(() => {
                  setNewSuggestionIndices(new Set());
                }, corrections.length * 150 + 500); // 150ms per suggestion + 500ms buffer
                
                onSuggestionsReceived?.(corrections);
              } catch (parseError) {
                console.error('Failed to parse corrections:', parseError);
                console.error('Content was:', chunk.content);
                setError('Failed to parse corrections from response');
              }
            }
          },
          onError: (err: Error) => {
            console.error('Streaming error:', err);
            setError(err.message);
            setIsLoading(false);
          },
          onComplete: () => {
            console.log('Stream completed');
            setIsLoading(false);
          },
        }
      );

      abortControllerRef.current = controller;
    } catch (err) {
      console.error('Request failed:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      setIsLoading(false);
    }
  }, [onSuggestionsReceived]);

  // Debounced version for typing (3 seconds)
  const debouncedRequestCorrections = useDebounce(requestCorrections, 3000);

  /**
   * Handle text change with debouncing
   */
  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value;
    onTextChange(newText);
    
    // If user is typing while suggestions are shown, those are now stale
    // The new request will cancel the old one and fetch fresh suggestions
    
    // Show preparing state immediately
    if (newText.trim()) {
      setIsPreparing(true);
    } else {
      setIsPreparing(false);
      setIsLoading(false);
    }
    
    debouncedRequestCorrections(newText);
  };

  /**
   * Handle manual correction button click (bypasses debounce)
   */
  const handleManualCorrect = () => {
    requestCorrections(text);
  };

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  /**
   * Handle clicks outside tooltip to close it
   */
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      // Don't close if clicking on a badge or inside the tooltip
      if (expandedSuggestionIndex !== null && 
          !target.closest('.inline-suggestion-card') && 
          !target.closest('.suggestion-badge')) {
        setExpandedSuggestionIndex(null);
        setTooltipPosition(null);
      }
    };

    if (expandedSuggestionIndex !== null) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [expandedSuggestionIndex]);

  /**
   * Sync scroll position between textarea and overlay
   */
  const handleScroll = () => {
    if (textareaRef.current && overlayRef.current) {
      overlayRef.current.scrollTop = textareaRef.current.scrollTop;
      overlayRef.current.scrollLeft = textareaRef.current.scrollLeft;
    }
  };

  /**
   * Render simple underline overlay for text with suggestions
   */
  const renderInlineOverlay = () => {
    if (!text || suggestions.length === 0) {
      return null;
    }

    // Create segments with just underlines (no ghost text)
    const segments: JSX.Element[] = [];
    let lastIndex = 0;

    // Sort suggestions by position
    const sortedSuggestions = [...suggestions].sort((a, b) => {
      const posA = a.start_position ?? text.indexOf(a.original_text);
      const posB = b.start_position ?? text.indexOf(b.original_text);
      return posA - posB;
    });

    sortedSuggestions.forEach((suggestion, index) => {
      const originalText = suggestion.original_text;
      const startPos = suggestion.start_position ?? text.indexOf(originalText, lastIndex);

      if (startPos !== -1 && startPos >= lastIndex) {
        // Add text before this suggestion (transparent)
        if (startPos > lastIndex) {
          segments.push(
            <span key={`before-${index}`} className="overlay-normal-text">
              {text.substring(lastIndex, startPos)}
            </span>
          );
        }

        // Add underlined text with badge (with animation class if new)
        const isNew = newSuggestionIndices.has(index);
        segments.push(
          <span 
            key={`suggestion-${index}`} 
            className={`overlay-underlined-text ${isNew ? 'suggestion-appear' : ''}`}
            style={isNew ? { animationDelay: `${index * 150}ms` } : undefined}
          >
            {originalText}
            <span 
              className="suggestion-badge"
              onClick={(e) => {
                e.stopPropagation();
                console.log('Badge clicked, current index:', expandedSuggestionIndex, 'clicked index:', index);
                
                // Calculate tooltip position based on badge position
                const target = e.currentTarget as HTMLElement;
                const rect = target.getBoundingClientRect();
                const scrollY = window.scrollY || window.pageYOffset;
                const scrollX = window.scrollX || window.pageXOffset;
                
                // Tooltip dimensions (estimated)
                const tooltipHeight = 300;
                const tooltipWidth = 350;
                const tooltipPadding = 20;
                
                // Calculate initial position below badge
                let top = rect.bottom + scrollY + 10;
                let left = Math.max(tooltipPadding, rect.left + scrollX - 150);
                
                // Check viewport boundaries
                const viewportHeight = window.innerHeight;
                const viewportWidth = window.innerWidth;
                
                // Prevent bottom overflow - show above badge if needed
                if (top + tooltipHeight > scrollY + viewportHeight) {
                  top = rect.top + scrollY - tooltipHeight - 10;
                }
                
                // Prevent right overflow
                if (left + tooltipWidth > viewportWidth) {
                  left = viewportWidth - tooltipWidth - tooltipPadding;
                }
                
                // Prevent left overflow (mobile)
                if (left < tooltipPadding) {
                  left = tooltipPadding;
                }
                
                setTooltipPosition({ top, left });
                setExpandedSuggestionIndex(expandedSuggestionIndex === index ? null : index);
              }}
              title="Click to view suggestion"
            >
              {index + 1}
            </span>
          </span>
        );

        lastIndex = startPos + originalText.length;
      }
    });

    // Add remaining text (transparent)
    if (lastIndex < text.length) {
      segments.push(
        <span key="remaining" className="overlay-normal-text">
          {text.substring(lastIndex)}
        </span>
      );
    }

    return (
      <div ref={overlayRef} className="inline-overlay">
        {segments}
      </div>
    );
  };

  /**
   * Render inline suggestion cards
   */
  const renderInlineSuggestionCards = () => {
    console.log('renderInlineSuggestionCards called, expandedIndex:', expandedSuggestionIndex, 'suggestions count:', suggestions.length);
    
    if (!text || suggestions.length === 0 || expandedSuggestionIndex === null || !tooltipPosition) {
      return null;
    }

    const suggestion = suggestions[expandedSuggestionIndex];
    console.log('Rendering card for suggestion:', suggestion);
    
    if (!suggestion) return null;

    const getTypeColor = (type: Correction['type']) => {
      const colorMap = {
        grammar: '#e74c3c',
        spelling: '#e67e22',
        style: '#3498db',
        tone: '#9b59b6',
        rephrasing: '#27ae60',
      };
      return colorMap[type] || '#95a5a6';
    };

    const getTypeIcon = (type: Correction['type']) => {
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
      <div 
        className="inline-suggestion-card"
        role="dialog"
        aria-label={`Correction suggestion: ${suggestion.type}`}
        aria-modal="true"
        style={{
          top: `${tooltipPosition.top}px`,
          left: `${tooltipPosition.left}px`
        }}
      >
        <div className="card-header">
          <span 
            className="card-type-badge"
            style={{ backgroundColor: getTypeColor(suggestion.type) }}
          >
            {getTypeIcon(suggestion.type)} {suggestion.type}
          </span>
          <button 
            className="card-close-btn"
            onClick={() => {
              setExpandedSuggestionIndex(null);
              setTooltipPosition(null);
            }}
            title="Close"
          >
            ✕
          </button>
        </div>
        
        <div className="card-content">
          <div className="card-text-change">
            <div className="original-line">
              <span className="label">Original:</span>
              <span className="text-value">{suggestion.original_text}</span>
            </div>
            <div className="arrow">↓</div>
            <div className="suggested-line">
              <span className="label">Suggested:</span>
              <span className="text-value">{suggestion.suggested_text}</span>
            </div>
          </div>
          
          {suggestion.explanation && (
            <div className="card-explanation">
              <strong>Why:</strong> {suggestion.explanation}
            </div>
          )}
        </div>
        
        <div className="card-actions">
          <button 
            className="card-action-btn accept"
            onClick={() => {
              // Apply the suggestion via parent component
              if (onAcceptSuggestion && expandedSuggestionIndex !== null) {
                onAcceptSuggestion(suggestion, expandedSuggestionIndex);
              } else {
                // Fallback: apply directly
                const newText = text.replace(suggestion.original_text, suggestion.suggested_text);
                onTextChange(newText);
              }
              setExpandedSuggestionIndex(null);
              setTooltipPosition(null);
            }}
          >
            Accept
          </button>
          <button 
            className="card-action-btn reject"
            onClick={() => {
              if (onRejectSuggestion && expandedSuggestionIndex !== null) {
                onRejectSuggestion(expandedSuggestionIndex);
              }
              setExpandedSuggestionIndex(null);
              setTooltipPosition(null);
            }}
          >
            Dismiss
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="text-editor-container">
      <div className="editor-header">
        <h2>Text Correction Editor</h2>
        <button
          className="manual-correct-btn"
          onClick={handleManualCorrect}
          disabled={isLoading || !text.trim()}
        >
          {isLoading ? 'Processing...' : 'Correct Text'}
        </button>
      </div>

      <div className="editor-wrapper">
        {renderInlineOverlay()}
        <textarea
          ref={textareaRef}
          className="text-input"
          value={text}
          onChange={handleTextChange}
          onScroll={handleScroll}
          placeholder="Start typing or paste your text here... (you can keep typing while suggestions load)"
          rows={15}
        />
        
        {(isLoading || isPreparing) && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <span>
              {isPreparing 
                ? 'Waiting to analyze...' 
                : streamChunks.length > 0 
                  ? `Streaming response... (${streamChunks.filter(c => c.type === 'chunk').length} chunks received)`
                  : 'Analyzing text...'}
            </span>
          </div>
        )}

        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}
      </div>

      {/* Backdrop overlay when tooltip is open */}
      {expandedSuggestionIndex !== null && tooltipPosition && (
        <div 
          className="tooltip-backdrop"
          role="presentation"
          aria-hidden="true" 
        />
      )}

      {/* Render expandable inline suggestion cards */}
      {renderInlineSuggestionCards()}

      {/* Streaming preview - shows real-time content */}
      {import.meta.env.DEV && isLoading && streamingContent && (
        <div className="streaming-preview">
          <h3>🔴 Live Stream (updating in real-time)</h3>
          <div className="streaming-content">
            <pre>{streamingContent}</pre>
            <div className="stream-indicator">
              <span className="pulse-dot"></span>
              Receiving data...
            </div>
          </div>
        </div>
      )}

      {/* Debug info - remove in production */}
      {import.meta.env.DEV && streamChunks.length > 0 && (
        <div className="debug-panel">
          <h3>Stream Debug Info</h3>
          <p>Total chunks received: {streamChunks.length}</p>
          <div className="chunk-list">
            {streamChunks.map((chunk, index) => (
              <div key={index} className="chunk-item">
                <span className="chunk-type">{chunk.type}</span>
                {chunk.content && (
                  <span className="chunk-content">
                    {chunk.content.substring(0, 50)}
                    {chunk.content.length > 50 ? '...' : ''}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TextEditor;
