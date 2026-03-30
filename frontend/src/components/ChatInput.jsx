import React from 'react';
import { Send } from 'lucide-react';

const ChatInput = ({ inputVal, setInputVal, handleChat, disabled, placeholder }) => {
  return (
    <div className="input-area">
      <div className="input-container">
        <input 
          type="text" 
          placeholder={placeholder} 
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleChat()}
          disabled={disabled}
        />
        <button 
          className="send-btn" 
          onClick={handleChat}
          disabled={!inputVal.trim() || disabled}
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
};

export default ChatInput;
