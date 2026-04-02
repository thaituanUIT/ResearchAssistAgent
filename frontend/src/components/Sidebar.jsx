import React from 'react';
import { UploadCloud, FileText, X, PlusCircle, MessageSquare, LogOut } from 'lucide-react';

const Sidebar = ({ 
  sessions,
  activeSession,
  onSelectSession,
  onNewSession,
  onLogout,
  files, 
  loading, 
  error, 
  fileInputRef, 
  onButtonClick, 
  handleChange, 
  handleDrop, 
  removeFile,
  username
}) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Sessions</h2>
        <button className="icon-btn" onClick={onNewSession} title="New Chat">
          <PlusCircle size={20} />
        </button>
      </div>
      
      <div className="papers-list" style={{ flex: 2, marginBottom: '20px' }}>
        {sessions.map((sess) => (
          <div 
            key={sess._id} 
            className="paper-item"
            onClick={() => onSelectSession(sess)}
            style={{ cursor: 'pointer', border: activeSession?._id === sess._id ? '1px solid var(--accent-primary)' : '', background: activeSession?._id === sess._id ? 'rgba(99, 102, 241, 0.1)' : '' }}
          >
            <MessageSquare size={16} style={{ color: activeSession?._id === sess._id ? 'var(--accent-primary)' : 'var(--text-secondary)' }} />
            <span className="paper-name">{sess.title}</span>
          </div>
        ))}
        {sessions.length === 0 && (
           <div className="empty-papers">No chat history</div>
        )}
      </div>

      <div className="sidebar-header" style={{ marginTop: 'auto', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '15px' }}>
        <h2>Auto Indexing</h2>
      </div>

      <div 
        className="empty-papers" 
        onClick={onButtonClick} 
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        style={{ cursor: 'pointer', marginBottom: '1rem', height: '80px', flexShrink: 0 }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
          <UploadCloud size={24} />
          {loading ? <span>Vectorizing...</span> : <span>Drop PDF to inject!</span>}
        </div>
        <input 
          type="file" 
          multiple 
          accept="application/pdf"
          ref={fileInputRef} 
          onChange={handleChange} 
          style={{ display: 'none' }} 
        />
      </div>

      {files.length > 0 && (
        <div className="papers-list" style={{ flex: 1 }}>
          {files.map((file, index) => (
            <div key={index} className="paper-item">
              <FileText size={18} />
              <span className="paper-name">{file.name}</span>
              <button className="del-btn" onClick={(e) => { e.stopPropagation(); removeFile(index); }}>
                <X size={16} />
              </button>
            </div>
          ))}
        </div>
      )}

      {error && (
        <div className="error-text">
          <X size={16} /> <span>{error}</span>
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
        <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Logged in as <strong style={{color:'var(--text-primary)'}}>{username}</strong></span>
        <button onClick={onLogout} className="del-btn" title="Logout" style={{background: 'rgba(239, 68, 68, 0.1)'}}>
          <LogOut size={16} />
        </button>
      </div>

    </aside>
  );
};

export default Sidebar;
