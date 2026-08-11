import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import './index.css';

// Random String Generator
const generateGuestId = () => 'guest_' + Math.random().toString(36).substr(2, 9);

function App() {
  const [guestId] = useState(() => {
    return localStorage.getItem('guestId') || generateGuestId();
  });

  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [messages, setMessages] = useState([]);
  const [inputVal, setInputVal] = useState('');
  const [isChatting, setIsChatting] = useState(false);

  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!localStorage.getItem('guestId')) {
      localStorage.setItem('guestId', guestId);
    }
    setMessages([{ role: 'agent', content: "Welcome to ResearchAssist. Attach a PDF and ask a research question to start." }]);
  }, [guestId]);

  const addFiles = (newFiles) => {
    const validFiles = Array.from(newFiles).filter(file => file.type === "application/pdf");
    if (validFiles.length < newFiles.length) {
      setError("Please only upload valid PDF files.");
    } else {
      setError(null);
    }
    setFiles(prev => [...prev, ...validFiles]);
    if (validFiles.length > 0) {
      performUpload(validFiles);
    }
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

  const performUpload = async (pdfFiles) => {
    setLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      pdfFiles.forEach(f => formData.append('files', f));
      formData.append('user_id', guestId);
      
      await axios.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      const updateMsg = { role: 'agent', content: `**Successfully Indexed Documents!**\n\nI have securely processed your uploaded papers into your vector memory. Feel free to ask me anything.` };
      
      setMessages(prev => [...prev, updateMsg]);
      
    } catch (err) {
      setError(err?.response?.data?.detail || "An error occurred during indexing.");
    } finally {
      setLoading(false);
    }
  };

  const handleChat = async () => {
    if (!inputVal.trim()) return;

    const newUserMsg = { role: 'user', content: inputVal };
    const currentMessages = [...messages, newUserMsg];
    
    setMessages(currentMessages);
    setInputVal('');
    setIsChatting(true);
    
    try {
      const aiResponse = await axios.post('/api/chat', {
        user_prompt: newUserMsg.content,
        chat_history: messages,
        user_id: guestId,
        session_id: 'local_session'
      });
      
      const newAgentMsg = {
        role: 'agent',
        content: aiResponse.data.chat_response,
        activeAgents: aiResponse.data.active_agents || [],
        intent: aiResponse.data.intent || null
      };
      const finalMessages = [...currentMessages, newAgentMsg];
      
      setMessages(finalMessages);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'agent', content: `*Error:* ${err?.response?.data?.detail || "Failed to process request."}` }]);
    } finally {
      setIsChatting(false);
    }
  };

  return (
    <div className="app-layout">
      <Sidebar 
        files={files}
        loading={loading}
        error={error}
        fileInputRef={fileInputRef}
        onButtonClick={onButtonClick}
        handleChange={handleChange}
        handleDrop={handleDrop}
        removeFile={removeFile}
      />

      <main className="main-content" style={{ display: 'flex', flexDirection: 'column' }}>
        <div className="header-bar">
          <button className="btn-secondary" onClick={() => setMessages([{ role: 'agent', content: "Started a fresh local session." }])}>
            New Chat
          </button>
        </div>
      
        <ChatWindow 
          messages={messages} 
          isChatting={isChatting} 
        />
        <ChatInput 
          inputVal={inputVal}
          setInputVal={setInputVal}
          handleChat={handleChat}
          disabled={isChatting}
          placeholder="Ask a question, or search Google Scholar..."
        />
      </main>
    </div>
  );
}

export default App;
