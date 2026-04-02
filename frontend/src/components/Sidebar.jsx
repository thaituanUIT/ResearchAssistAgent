import React from 'react';
import { FileText, X, AlertCircle, Paperclip } from 'lucide-react';

const Sidebar = ({ 
  files, 
  loading, 
  error, 
  fileInputRef, 
  onButtonClick, 
  handleChange, 
  handleDrop, 
  removeFile,
  uploadInstruction,
  setUploadInstruction
}) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Papers</h2>
        <button className="icon-btn" onClick={onButtonClick} title="Upload Paper">
          <Paperclip size={18} />
        </button>
        <input 
          ref={fileInputRef} 
          type="file" 
          accept="application/pdf" 
          multiple 
          onChange={handleChange} 
          style={{display: 'none'}} 
        />
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
            <button className="del-btn" onClick={() => removeFile(idx)}>
              <X size={14} />
            </button>
          </div>
        ))}
        {files.length === 0 && (
          <div className="empty-papers">
            <p>Drag and drop PDFs here</p>
          </div>
        )}
      </div>

      {error && (
        <div className="error-text">
          <AlertCircle size={14}/> {error}
        </div>
      )}

      <div style={{ display: 'none', padding: '0 20px', marginBottom: '15px' }}>
        <textarea 
          style={{ width: '100%', minHeight: '60px', borderRadius: '4px', padding: '8px', border: '1px solid #444', background: '#222', color: '#eee', fontSize: '13px', resize: 'vertical' }}
          placeholder="Optional: Ask to create a flowchart, compare methods, etc..."
          value={uploadInstruction}
          onChange={(e) => setUploadInstruction(e.target.value)}
          disabled={loading}
        />
      </div>

    </aside>
  );
};

export default Sidebar;
