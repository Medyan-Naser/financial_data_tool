import React, { useState, useRef, useEffect } from 'react';

function ResizablePanel({ children, minWidth = 300, minHeight = 200, defaultWidth = 600, defaultHeight = 400 }) {
  const [size, setSize] = useState({ width: defaultWidth, height: defaultHeight });
  const [isResizing, setIsResizing] = useState({ horizontal: false, vertical: false, corner: false });
  const panelRef = useRef(null);
  const startPos = useRef({ x: 0, y: 0, width: 0, height: 0 });

  const handleMouseDown = (type) => (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    const rect = panelRef.current.getBoundingClientRect();
    startPos.current = {
      x: e.clientX,
      y: e.clientY,
      width: rect.width,
      height: rect.height
    };

    setIsResizing({
      horizontal: type === 'horizontal' || type === 'corner',
      vertical: type === 'vertical' || type === 'corner',
      corner: type === 'corner'
    });
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing.horizontal && !isResizing.vertical) return;

      const deltaX = e.clientX - startPos.current.x;
      const deltaY = e.clientY - startPos.current.y;

      setSize(prev => ({
        width: isResizing.horizontal 
          ? Math.max(minWidth, startPos.current.width + deltaX)
          : prev.width,
        height: isResizing.vertical 
          ? Math.max(minHeight, startPos.current.height + deltaY)
          : prev.height
      }));
    };

    const handleMouseUp = () => {
      setIsResizing({ horizontal: false, vertical: false, corner: false });
    };

    if (isResizing.horizontal || isResizing.vertical) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, minWidth, minHeight]);

  return (
    <div 
      ref={panelRef}
      className="resizable-panel"
      style={{ 
        width: `${size.width}px`, 
        height: `${size.height}px`,
        position: 'relative'
      }}
    >
      {children}
      
      {/* Right resize handle */}
      <div 
        className="resize-handle-right"
        onMouseDown={handleMouseDown('horizontal')}
      />
      
      {/* Bottom resize handle */}
      <div 
        className="resize-handle-bottom"
        onMouseDown={handleMouseDown('vertical')}
      />
      
      {/* Corner resize handle */}
      <div 
        className="resize-handle-corner"
        onMouseDown={handleMouseDown('corner')}
      />
    </div>
  );
}

export default ResizablePanel;
