import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { Upload, FileText, CheckCircle, MessageSquare, AlertCircle, Loader2, X, Activity, RefreshCw, Send, Paperclip } from 'lucide-react';
import './index.css';

function App() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Chat state
  const [messages, setMessages] = useState([]); // { role: 'user' | 'agent', content: string }
  const [inputVal, setInputVal] = useState('');
  const [isChatting, setIsChatting] = useState(false);
  
  // Context state from original upload
  const [documentContext, setDocumentContext] = useState({
    working_document: '',
    synthesis: ''
  });

  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addFiles = (newFiles) => {
    const validFiles = Array.from(newFiles).filter(file => file.type === "application/pdf");
    if (validFiles.length < newFiles.length) {
      setError("Please only upload valid PDF files.");
    } else {
      setError(null);
    }
    setFiles(prev => [...prev, ...validFiles]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files?.length > 0) addFiles(e.dataTransfer.files);
  };
  const handleChange = (e) => {
    if (e.target.files?.length > 0) addFiles(e.target.files);
  };
  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };
  const onButtonClick = () => fileInputRef.current.click();

  const handleAnalyze = async () => {
    if (files.length === 0) return;
    setLoading(true);
    setError(null);
    setMessages([]);
    
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    
    try {
      const response = await axios.post('http://localhost:8000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      // Save context
      setDocumentContext({
        working_document: response.data.working_document || '',
        synthesis: response.data.synthesis || ''
      });
      // Add first agent message
      setMessages([
        { 
          role: 'agent', 
          content: `**Analysis Complete!**\n\nThe papers have been routed through the graph and parsed. I generated a final synthesis report.\n\n--- \n ${response.data.synthesis}\n\n--- \n Feel free to ask me any questions regarding the uploaded documents.` 
        }
      ]);
    } catch (err) {
      setError(err.response?.data?.detail || "An error occurred during analysis.");
    } finally {
      setLoading(false);
    }
  };

  const handleChat = async () => {
    if (!inputVal.trim()) return;
    
    const newUserMsg = { role: 'user', content: inputVal };
    const chatHistory = [...messages, newUserMsg];
    
    setMessages(chatHistory);
    setInputVal('');
    setIsChatting(true);
    
    try {
      const response = await axios.post('http://localhost:8000/chat', {
        user_prompt: newUserMsg.content,
        chat_history: messages,
        working_document: documentContext.working_document,
        synthesis: documentContext.synthesis
      });
      
      setMessages(prev => [...prev, { role: 'agent', content: response.data.chat_response }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'agent', content: `*Error:* ${err.response?.data?.detail || "Failed to process question."}` }]);
    } finally {
      setIsChatting(false);
    }
  };

  return (
    <div className="app-layout">
      {/* LEFT SIDEBAR */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>Papers</h2>
          <button className="icon-btn" onClick={onButtonClick} title="Upload Paper"><Paperclip size={18} /></button>
          <input ref={fileInputRef} type="file" accept="application/pdf" multiple onChange={handleChange} style={{display: 'none'}} />
        </div>
        
        <div 
          className="papers-list"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
        >
          {files.map((file, idx) => (
            <div key={idx} className="paper-item">
              <FileText size={16} />
              <span className="paper-name" title={file.name}>{file.name}</span>
              <button className="del-btn" onClick={() => removeFile(idx)}><X size={14} /></button>
            </div>
          ))}
          {files.length === 0 && (
            <div className="empty-papers">
              <p>Drag and drop PDFs here</p>
            </div>
          )}
        </div>

        {error && <div className="error-text"><AlertCircle size={14}/> {error}</div>}

        <button 
          className="btn-primary full-width mt-auto" 
          onClick={handleAnalyze} 
          disabled={files.length === 0 || loading}
        >
          {loading ? "Analyzing..." : "Analyze Papers"}
        </button>
      </aside>

      {/* MAIN CHAT AREA */}
      <main className="main-content">
        <div className="chat-window">
          {messages.length === 0 ? (
            <div className="empty-state">
              <MessageSquare size={48} className="glow-icon" />
              <h3>Welcome to ResearchAssist</h3>
              <p>Upload your research papers in the sidebar and click "Analyze Papers" to begin chatting.</p>
            </div>
          ) : (
            <div className="messages-container">
              {messages.map((msg, idx) => (
                <div key={idx} className={`message-row ${msg.role}`}>
                  <div className={`message-bubble ${msg.role}`}>
                    <div className="message-sender">{msg.role === 'agent' ? 'ResearchAssist' : 'You'}</div>
                    <div className="markdown-body">
                      {msg.role === 'agent' ? <ReactMarkdown>{msg.content}</ReactMarkdown> : msg.content}
                    </div>
                  </div>
                </div>
              ))}
              {isChatting && (
                <div className="message-row agent">
                  <div className="message-bubble agent">
                    <div className="spinner-small"></div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* INPUT AREA */}
        <div className="input-area">
          <div className="input-container">
            <input 
              type="text" 
              placeholder={documentContext.synthesis ? "Ask a question about your papers..." : "Upload and analyze papers first..."} 
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleChat()}
              disabled={!documentContext.synthesis || isChatting}
            />
            <button 
              className="send-btn" 
              onClick={handleChat}
              disabled={!inputVal.trim() || !documentContext.synthesis || isChatting}
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
