import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { MessageSquare } from 'lucide-react';
import Mermaid from './Mermaid';

const ChatWindow = ({ messages, isChatting }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isChatting]);

  return (
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
                <div className="message-sender">
                  {msg.role === 'agent' ? 'ResearchAssist' : 'You'}
                </div>
                <div className="markdown-body">
                  {msg.role === 'agent' ? (
                    <ReactMarkdown
                      components={{
                        code({ node, inline, className, children, ...props }) {
                          const match = /language-(\w+)/.exec(className || '');
                          if (!inline && match && match[1] === 'mermaid') {
                            return <Mermaid chart={String(children).replace(/\n$/, '')} />;
                          }
                          return (
                            <code className={className} {...props}>
                              {children}
                            </code>
                          );
                        }
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  ) : (
                    msg.content
                  )}
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
  );
};

export default ChatWindow;
