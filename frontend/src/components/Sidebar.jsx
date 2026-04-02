import React from 'react';
import { UploadCloud, FileText, X } from 'lucide-react';

const Sidebar = ({ 
  files, 
  loading, 
  error, 
  fileInputRef, 
  onButtonClick, 
  handleChange, 
  handleDrop, 
  removeFile
}) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Auto Indexing</h2>
      </div>

      <div 
        className="empty-papers" 
        onClick={onButtonClick} 
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        style={{ cursor: 'pointer', marginBottom: '1rem', height: '100px', flexShrink: 0 }}
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
    </aside>
  );
};

export default Sidebar;
