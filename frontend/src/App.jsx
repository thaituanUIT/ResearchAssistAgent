import React, { useState, useRef } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import { uploadPapers, sendChatMessage } from './services/api';
import './index.css';

function App() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadInstruction, setUploadInstruction] = useState('');
  
  // Chat state
  const [messages, setMessages] = useState([]);
  const [inputVal, setInputVal] = useState('');
  const [isChatting, setIsChatting] = useState(false);
  
  // Context state from original upload
  const [documentContext, setDocumentContext] = useState({
    working_document: '',
    synthesis: ''
  });

  const fileInputRef = useRef(null);

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
    
    try {
      const data = await uploadPapers(files, uploadInstruction);
      setDocumentContext({
        working_document: data.working_document || '',
        synthesis: data.synthesis || ''
      });
      setMessages([
        { 
          role: 'agent', 
          content: `**Analysis Complete!**\n\nThe papers have been parsed. I generated a final synthesis report.\n\n--- \n ${data.synthesis}\n\n--- \n Feel free to ask me any questions regarding the uploaded documents.` 
        }
      ]);
    } catch (err) {
      setError(err?.response?.data?.detail || "An error occurred during analysis.");
    } finally {
      setLoading(false);
    }
  };

  const handleChat = async () => {
    if (!inputVal.trim()) return;
    
    const newUserMsg = { role: 'user', content: inputVal };
    const currentMessages = [...messages];
    const newChatHistory = [...messages, newUserMsg];
    
    setMessages(newChatHistory);
    setInputVal('');
    setIsChatting(true);
    
    try {
      const data = await sendChatMessage(
        newUserMsg.content,
        currentMessages,
        documentContext.working_document,
        documentContext.synthesis
      );
      
      setMessages(prev => [...prev, { role: 'agent', content: data.chat_response }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'agent', content: `*Error:* ${err?.response?.data?.detail || "Failed to process question."}` }]);
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
        handleAnalyze={handleAnalyze}
        uploadInstruction={uploadInstruction}
        setUploadInstruction={setUploadInstruction}
      />

      <main className="main-content">
        <ChatWindow 
          messages={messages} 
          isChatting={isChatting} 
        />
        <ChatInput 
          inputVal={inputVal}
          setInputVal={setInputVal}
          handleChat={handleChat}
          disabled={!documentContext.synthesis || isChatting}
          placeholder={documentContext.synthesis ? "Ask a question about your papers..." : "Upload and analyze papers first..."}
        />
      </main>
    </div>
  );
}

export default App;
