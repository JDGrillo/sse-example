import { useState } from 'react';
import TextEditor from './components/TextEditor';
import SuggestionRenderer from './components/SuggestionRenderer';
import type { Correction } from './types/corrections';
import './App.css';

function App() {
  const [text, setText] = useState('');
  const [suggestions, setSuggestions] = useState<Correction[]>([]);

  const handleTextChange = (newText: string) => {
    setText(newText);
  };

  const handleSuggestionsReceived = (newSuggestions: Correction[]) => {
    console.log('Suggestions received in App:', newSuggestions);
    setSuggestions(newSuggestions);
  };

  const handleAcceptSuggestion = (suggestion: Correction, index: number) => {
    console.log('Accepting suggestion:', suggestion);
    
    // Replace original text with suggested text
    const newText = text.replace(suggestion.original_text, suggestion.suggested_text);
    setText(newText);
    
    // Remove the accepted suggestion from the list
    setSuggestions(prev => prev.filter((_, i) => i !== index));
  };

  const handleRejectSuggestion = (index: number) => {
    console.log('Rejecting suggestion at index:', index);
    setSuggestions(prev => prev.filter((_, i) => i !== index));
  };

  const handleAcceptAll = () => {
    console.log('Accepting all suggestions');
    let newText = text;
    
    // Apply all suggestions
    suggestions.forEach(suggestion => {
      newText = newText.replace(suggestion.original_text, suggestion.suggested_text);
    });
    
    setText(newText);
    setSuggestions([]);
  };

  const handleRejectAll = () => {
    console.log('Rejecting all suggestions');
    setSuggestions([]);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Text Correction App</h1>
        <p>Powered by Microsoft Foundry & GPT-4o</p>
      </header>
      
      <main className="app-main">
        <TextEditor 
          text={text}
          suggestions={suggestions}
          onTextChange={handleTextChange}
          onSuggestionsReceived={handleSuggestionsReceived}
          onAcceptSuggestion={handleAcceptSuggestion}
          onRejectSuggestion={handleRejectSuggestion}
        />
        
        <SuggestionRenderer
          suggestions={suggestions}
          onAccept={handleAcceptSuggestion}
          onReject={handleRejectSuggestion}
          onAcceptAll={handleAcceptAll}
          onRejectAll={handleRejectAll}
        />
      </main>
    </div>
  );
}

export default App;
