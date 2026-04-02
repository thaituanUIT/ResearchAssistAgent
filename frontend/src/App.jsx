import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import Auth from './components/Auth';
import './index.css';

// Random String Generator
const generateGuestId = () => 'guest_' + Math.random().toString(36).substr(2, 9);

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user')) || null);
  
  // Guest ID context
  const [guestId, setGuestId] = useState(() => {
    return localStorage.getItem('guestId') || generateGuestId();
  });
  
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [messages, setMessages] = useState([]);
  const [inputVal, setInputVal] = useState('');
  const [isChatting, setIsChatting] = useState(false);
  
  const [showAuthModal, setShowAuthModal] = useState(false);
  
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!localStorage.getItem('guestId')) {
      localStorage.setItem('guestId', guestId);
    }
    
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchSessions();
    } else {
      // Guest mode setup
      setSessions([]);
      setActiveSession(null);
      setMessages([{ role: 'agent', content: "Welcome to ResearchAssist! You are currently using Guest Mode. Your chats will not be saved locally, but you can feel free to attach a PDF and query our AI immediately. \n\nLog in anywhere at any time to save!" }]);
    }
  }, [token]);

  const fetchSessions = async () => {
    try {
      const { data } = await axios.get('http://localhost:5000/api/sessions');
      setSessions(data);
      if (data.length > 0 && !activeSession) {
        selectSession(data[0]);
      } else if (data.length === 0) {
        createNewSession();
      }
    } catch (err) {
      console.error(err);
      if (err.response?.status === 401) handleLogout();
    }
  };

  const createNewSession = async () => {
    if (!token) return; // DB interaction blocked for guest
    try {
      const { data } = await axios.post('http://localhost:5000/api/sessions', { title: 'New Chat' });
      setSessions([data, ...sessions]);
      selectSession(data);
    } catch (err) {
      console.error(err);
    }
  };

  const selectSession = (session) => {
    setActiveSession(session);
    setMessages(session.messages || []);
  };

  const clearGuestChat = () => {
    setMessages([{ role: 'agent', content: "Started a fresh Guest Session." }]);
  };

  const handleLogin = (userData) => {
    setShowAuthModal(false);
    setToken(userData.token);
    setUser(userData);
    localStorage.setItem('token', userData.token);
    localStorage.setItem('user', JSON.stringify(userData));
    // Clear ephemeral guest chat from screen. 
    setMessages([]);
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    setActiveSession(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
  };

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
      const currentUserId = user?._id || guestId;
      const formData = new FormData();
      pdfFiles.forEach(f => formData.append('files', f));
      formData.append('user_id', currentUserId);
      
      await axios.post('http://localhost:8000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      const updateMsg = { role: 'agent', content: `**Successfully Indexed Documents!**\n\nI have securely processed your uploaded papers into your vector memory. Feel free to ask me anything.` };
      
      setMessages(prev => [...prev, updateMsg]);
      
      if (token && activeSession) {
        await axios.put(`http://localhost:5000/api/sessions/${activeSession._id}`, {
          messages: [...messages, updateMsg]
        });
      }
      
    } catch (err) {
      setError(err?.response?.data?.detail || "An error occurred during indexing.");
    } finally {
      setLoading(false);
    }
  };

  const handleChat = async () => {
    if (!inputVal.trim()) return;
    // Guest block active session restriction
    if (token && !activeSession) return;
    
    const newUserMsg = { role: 'user', content: inputVal };
    const currentMessages = [...messages, newUserMsg];
    
    setMessages(currentMessages);
    setInputVal('');
    setIsChatting(true);
    
    try {
      if (token && activeSession) {
        await axios.put(`http://localhost:5000/api/sessions/${activeSession._id}`, {
          messages: currentMessages,
          title: activeSession.title === 'New Chat' ? newUserMsg.content.substring(0, 20) + "..." : activeSession.title
        });
      }

      const currentUserId = user?._id || guestId;
      const aiResponse = await axios.post('http://localhost:8000/chat', {
        user_prompt: newUserMsg.content,
        chat_history: messages, // Send full array context
        user_id: currentUserId,
        session_id: token ? activeSession._id : 'guest_session'
      });
      
      const newAgentMsg = { role: 'agent', content: aiResponse.data.chat_response };
      const finalMessages = [...currentMessages, newAgentMsg];
      
      setMessages(finalMessages);
      
      if (token && activeSession) {
        await axios.put(`http://localhost:5000/api/sessions/${activeSession._id}`, {
          messages: finalMessages
        });
        fetchSessions();
      }
      
    } catch (err) {
      setMessages(prev => [...prev, { role: 'agent', content: `*Error:* ${err?.response?.data?.detail || "Failed to process request."}` }]);
    } finally {
      setIsChatting(false);
    }
  };

  return (
    <div className="app-layout">
      {showAuthModal && (
        <Auth onLogin={handleLogin} onClose={() => setShowAuthModal(false)} />
      )}
      
      <Sidebar 
        sessions={sessions}
        activeSession={activeSession}
        onSelectSession={selectSession}
        onNewSession={token ? createNewSession : clearGuestChat}
        onLogout={handleLogout}
        files={files}
        loading={loading}
        error={error}
        fileInputRef={fileInputRef}
        onButtonClick={onButtonClick}
        handleChange={handleChange}
        handleDrop={handleDrop}
        removeFile={removeFile}
        username={token ? user?.username : 'Guest'}
        isGuest={!token}
      />

      <main className="main-content" style={{ display: 'flex', flexDirection: 'column' }}>
        <div className="header-bar">
          {!token ? (
            <>
              <button className="btn-secondary" onClick={() => setShowAuthModal(true)}>Log in</button>
              <button className="btn-primary" onClick={() => setShowAuthModal(true)}>Sign Up</button>
            </>
          ) : (
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              Syncing to Cloud • Valid Session
            </div>
          )}
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
