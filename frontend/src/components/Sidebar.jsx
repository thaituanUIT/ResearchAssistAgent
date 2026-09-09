import React from 'react';
import { Cloud, Cpu, FileText, Server, UploadCloud, X } from 'lucide-react';

const Sidebar = ({ 
  files, 
  loading, 
  error, 
  fileInputRef, 
  onButtonClick, 
  handleChange, 
  handleDrop, 
  removeFile,
  modelStatus
}) => {
  const isLocal = modelStatus?.provider === 'local';
  const isConnected = modelStatus?.status === 'connected' || modelStatus?.status === 'not_checked';

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Auto Indexing</h2>
      </div>

      <div className="model-panel">
        <div className="model-panel-title">
          {isLocal ? <Cpu size={18} /> : <Cloud size={18} />}
          <span>{isLocal ? 'Local Model' : 'Cloud Model'}</span>
        </div>
        <div className="model-name">{modelStatus?.model || 'Checking model...'}</div>
        {modelStatus?.base_url && (
          <div className="model-url">{modelStatus.base_url}</div>
        )}
        <div className={`model-status ${isConnected ? 'ok' : 'error'}`}>
          <Server size={14} />
          <span>{modelStatus?.status || 'checking'}</span>
        </div>
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
