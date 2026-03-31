import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: true,
  theme: 'default',
  securityLevel: 'loose',
});

const Mermaid = ({ chart }) => {
  const containerRef = useRef(null);

  useEffect(() => {
    let isMounted = true;
    if (chart && containerRef.current) {
      containerRef.current.innerHTML = ''; // Clear previous render
      const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;
      mermaid.render(id, chart)
        .then(({ svg }) => {
          if (isMounted && containerRef.current) {
            containerRef.current.innerHTML = svg;
          }
        })
        .catch((error) => {
          console.error("Mermaid parsing error:", error);
          if (isMounted && containerRef.current) {
            containerRef.current.innerHTML = `<div class="error-text" style="color: red; padding: 10px;">Failed to render flowchart. The AI might have generated invalid syntax.</div>`;
          }
        });
    }
    return () => {
      isMounted = false;
    };
  }, [chart]);

  return <div className="mermaid-container" ref={containerRef} style={{ background: 'white', padding: '15px', borderRadius: '8px', overflowX: 'auto' }} />;
};

export default Mermaid;
