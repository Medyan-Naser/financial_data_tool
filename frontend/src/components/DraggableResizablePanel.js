import React, { useState, useRef, useEffect } from 'react';

function DraggableResizablePanel({ 
  children, 
  id,
  position,
  size,
  onPositionChange,
  onSizeChange,
  minWidth = 300, 
  minHeight = 200,
  showAlignmentGuides,
  alignmentGuides = [],
  zIndex = 1,
  onFocus
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState({ horizontal: false, vertical: false, corner: false });
  const panelRef = useRef(null);
  const dragStartPos = useRef({ x: 0, y: 0, panelX: 0, panelY: 0 });
  const resizeStartPos = useRef({ x: 0, y: 0, width: 0, height: 0 });

  // Handle drag start
  const handleDragStart = (e) => {
    // Only drag if clicking on the header/handle area
    if (!e.target.classList.contains('drag-handle')) return;
    
    e.preventDefault();
    e.stopPropagation();
    
    // Notify parent that this panel is now active
    if (onFocus) onFocus(id);
    
    dragStartPos.current = {
      x: e.clientX,
      y: e.clientY,
      panelX: position.x,
      panelY: position.y
    };
    
    setIsDragging(true);
  };

  // Handle resize start
  const handleResizeStart = (type) => (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Notify parent that this panel is now active
    if (onFocus) onFocus(id);
    
    resizeStartPos.current = {
      x: e.clientX,
      y: e.clientY,
      width: size.width,
      height: size.height
    };

    setIsResizing({
      horizontal: type === 'horizontal' || type === 'corner',
      vertical: type === 'vertical' || type === 'corner',
      corner: type === 'corner'
    });
  };

  // Handle mouse move for dragging
  useEffect(() => {
    if (!isDragging) return;

    const handleDragMove = (e) => {
      e.preventDefault();
      
      const deltaX = e.clientX - dragStartPos.current.x;
      const deltaY = e.clientY - dragStartPos.current.y;

      let newX = dragStartPos.current.panelX + deltaX;
      let newY = dragStartPos.current.panelY + deltaY;

      // Snap to alignment guides (within 10px threshold)
      const snapThreshold = 10;
      alignmentGuides.forEach(guide => {
        if (guide.type === 'vertical') {
          if (Math.abs(newX - guide.position) < snapThreshold) {
            newX = guide.position;
          }
          if (Math.abs((newX + size.width) - guide.position) < snapThreshold) {
            newX = guide.position - size.width;
          }
        } else if (guide.type === 'horizontal') {
          if (Math.abs(newY - guide.position) < snapThreshold) {
            newY = guide.position;
          }
          if (Math.abs((newY + size.height) - guide.position) < snapThreshold) {
            newY = guide.position - size.height;
          }
        }
      });

      // Keep within viewport bounds (more generous bounds)
      newX = Math.max(-size.width + 100, Math.min(newX, window.innerWidth - 100));
      newY = Math.max(0, newY);

      onPositionChange({ x: newX, y: newY });
    };

    const handleDragEnd = (e) => {
      e.preventDefault();
      setIsDragging(false);
    };

    document.addEventListener('mousemove', handleDragMove, true);
    document.addEventListener('mouseup', handleDragEnd, true);

    return () => {
      document.removeEventListener('mousemove', handleDragMove, true);
      document.removeEventListener('mouseup', handleDragEnd, true);
    };
  }, [isDragging, size, alignmentGuides, onPositionChange]);

  // Handle mouse move for resizing
  useEffect(() => {
    if (!isResizing.horizontal && !isResizing.vertical) return;

    const handleResizeMove = (e) => {
      e.preventDefault();

      const deltaX = e.clientX - resizeStartPos.current.x;
      const deltaY = e.clientY - resizeStartPos.current.y;

      const newSize = {
        width: isResizing.horizontal 
          ? Math.max(minWidth, resizeStartPos.current.width + deltaX)
          : size.width,
        height: isResizing.vertical 
          ? Math.max(minHeight, resizeStartPos.current.height + deltaY)
          : size.height
      };

      onSizeChange(newSize);
    };

    const handleResizeEnd = (e) => {
      e.preventDefault();
      setIsResizing({ horizontal: false, vertical: false, corner: false });
    };

    document.addEventListener('mousemove', handleResizeMove, true);
    document.addEventListener('mouseup', handleResizeEnd, true);

    return () => {
      document.removeEventListener('mousemove', handleResizeMove, true);
      document.removeEventListener('mouseup', handleResizeEnd, true);
    };
  }, [isResizing, minWidth, minHeight, onSizeChange]);

  // Handle panel click to bring to front
  const handlePanelClick = (e) => {
    // Always bring panel to front on any click
    if (onFocus) onFocus(id);
  };

  // Handle mousedown to bring to front immediately
  const handlePanelMouseDown = (e) => {
    // Bring to front as soon as mouse is pressed
    if (onFocus) onFocus(id);
  };

  return (
    <div 
      ref={panelRef}
      className={`draggable-resizable-panel ${isDragging ? 'dragging' : ''} ${isResizing.horizontal || isResizing.vertical ? 'resizing' : ''}`}
      style={{ 
        position: 'absolute',
        left: `${position.x}px`,
        top: `${position.y}px`,
        width: `${size.width}px`, 
        height: `${size.height}px`,
        zIndex: isDragging || isResizing.horizontal || isResizing.vertical ? 1000 : zIndex
      }}
      onMouseDown={handlePanelMouseDown}
      onClick={handlePanelClick}
    >
      {/* Drag Handle */}
      <div 
        className="drag-handle"
        onMouseDown={handleDragStart}
        title="Drag to move"
      >
        <span className="drag-handle-icon">⋮⋮</span>
      </div>

      {/* Content */}
      <div className="panel-content">
        {children}
      </div>
      
      {/* Resize Handles */}
      <div 
        className="resize-handle-right"
        onMouseDown={handleResizeStart('horizontal')}
      />
      
      <div 
        className="resize-handle-bottom"
        onMouseDown={handleResizeStart('vertical')}
      />
      
      <div 
        className="resize-handle-corner"
        onMouseDown={handleResizeStart('corner')}
      />
    </div>
  );
}

export default DraggableResizablePanel;
