import React, { useState, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { Upload, FileText, CheckCircle, MessageSquare, AlertCircle, Loader2, X, Activity, RefreshCw } from 'lucide-react';
import './index.css';

function App() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const addFiles = (newFiles) => {
    const validFiles = Array.from(newFiles).filter(file => file.type === "application/pdf");
    if (validFiles.length < newFiles.length) {
      setError("Some files were skipped. Please only upload valid PDF files.");
    } else {
      setError(null);
    }
    setFiles(prev => [...prev, ...validFiles]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files.length > 0) {
      addFiles(e.target.files);
    }
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const onButtonClick = () => {
    fileInputRef.current.click();
  };

  const handleAnalyze = async () => {
    if (files.length === 0) return;
    
    setLoading(true);
    setError(null);
    setResults(null);
    
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    
    try {
      const response = await axios.post('http://localhost:8000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setResults(response.data);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "An error occurred during analysis.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header>
        <h1>ResearchAssist</h1>
        <p className="subtitle">AI-Powered Notebook & Paper Analyst</p>
      </header>

      <div className="glass-panel main-panel">
        <div className="card-title">
          <Upload size={24} />
          <span>Upload Notebook Papers (PDFs)</span>
        </div>
        
        <div 
          className={`upload-area ${dragActive ? 'drag-active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={onButtonClick}
        >
          <input 
            ref={fileInputRef}
            type="file" 
            accept="application/pdf" 
            multiple
            onChange={handleChange} 
          />
          <FileText className="upload-icon" />
          <div>
            <p style={{ fontSize: '1.2rem', fontWeight: 500, color: 'var(--text-primary)' }}>Drag and drop your PDFs here</p>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>or click to browse from your computer</p>
          </div>
        </div>

        {files.length > 0 && (
          <div className="files-list">
            <h4 style={{marginBottom: '0.5rem', color: 'var(--text-primary)'}}>Selected Notebook Files:</h4>
            <div className="files-grid">
              {files.map((file, idx) => (
                <div key={idx} className="file-chip">
                  <FileText size={16} style={{flexShrink: 0, color: 'var(--primary)'}} />
                  <span className="file-name" title={file.name}>{file.name}</span>
                  <button className="del-btn" onClick={(e) => { e.stopPropagation(); removeFile(idx); }}><X size={16} /></button>
                </div>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="error-msg" style={{ marginTop: '1rem', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center' }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '1.5rem' }}>
          <button 
            className="btn-primary" 
            onClick={handleAnalyze}
            disabled={files.length === 0 || loading}
          >
            {loading ? (
              <>
                <div className="spinner"></div>
                Analyzing Papers...
              </>
            ) : "Analyze Notebook"}
          </button>
        </div>
      </div>

      {results && (
        <div className={`dashboard-grid ${results ? 'has-results' : ''}`}>
          
          <div className="glass-panel" style={{ animationDelay: '0.1s', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="card-title">
              <Activity size={24} />
              <span>Graph Execution Route</span>
            </div>
            <div className="route-info">
              <div className="route-tag">
                <span className="label">Route Mode:</span> 
                <span className={`val ${results.route === 'complex' ? 'complex' : 'simple'}`}>{results.route.toUpperCase()}</span>
              </div>
              <div className="route-tag">
                <span className="label">Evaluation Check:</span> 
                <span className={`val ${results.confidence_level === 'high' ? 'high' : 'low'}`}>{results.confidence_level.toUpperCase()} Confidence</span>
              </div>
              {results.retrieved_context && (
                <div className="route-tag" style={{marginTop: '0.5rem', background: 'rgba(245, 158, 11, 0.1)', padding: '0.5rem', borderRadius: '8px', border: '1px solid rgba(245, 158, 11, 0.3)'}}>
                  <RefreshCw size={18} style={{color: '#f59e0b'}} />
                  <span className="val" style={{color: '#f59e0b'}}>Retriever Node Engaged for missing context</span>
                </div>
              )}
            </div>
          </div>

          <div className="glass-panel synth-panel" style={{ animationDelay: '0.3s' }}>
            <div className="card-title">
              <MessageSquare size={24} />
              <span>Final Synthesis Report</span>
            </div>
            <div className="tag" style={{ background: 'rgba(217, 70, 239, 0.15)', color: '#f0abfc' }}>
              Role: The Synthesizer
            </div>
            <div className="markdown-body">
              <ReactMarkdown>{results.synthesis}</ReactMarkdown>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
