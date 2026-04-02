import React from 'react';
import { PlusCircle, MessageSquare, LogOut } from 'lucide-react';

const SessionSidebar = ({ 
  sessions,
  activeSession,
  onSelectSession,
  onNewSession,
  onLogout,
  username,
  isGuest
}) => {
  return (
    <aside className="session-sidebar">
      <div className="sidebar-header">
        <h2>Sessions</h2>
        <button className="icon-btn" onClick={onNewSession} title="New Chat">
          <PlusCircle size={20} />
        </button>
      </div>
      
      <div className="papers-list" style={{ flex: 1, marginBottom: '20px' }}>
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
           <div className="empty-papers" style={{ height: '70px' }}>
              {isGuest ? "Login to save chat history." : "No chat history"}
           </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
        <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Logged in as <strong style={{color:'var(--text-primary)'}}>{username}</strong></span>
        {!isGuest && (
        <button onClick={onLogout} className="del-btn" title="Logout" style={{background: 'rgba(239, 68, 68, 0.1)'}}>
          <LogOut size={16} />
        </button>
        )}
      </div>
    </aside>
  );
};

export default SessionSidebar;
