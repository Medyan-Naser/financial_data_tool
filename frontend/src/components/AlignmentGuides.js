import React from 'react';

function AlignmentGuides({ guides, show }) {
  if (!show || guides.length === 0) return null;

  return (
    <div className="alignment-guides-container">
      {guides.map((guide, index) => (
        <div
          key={index}
          className={`alignment-guide ${guide.type}`}
          style={{
            position: 'fixed',
            [guide.type === 'vertical' ? 'left' : 'top']: `${guide.position}px`,
            [guide.type === 'vertical' ? 'top' : 'left']: 0,
            [guide.type === 'vertical' ? 'bottom' : 'right']: 0,
            [guide.type === 'vertical' ? 'width' : 'height']: '1px',
            backgroundColor: '#667eea',
            opacity: 0.7,
            pointerEvents: 'none',
            zIndex: 9999
          }}
        />
      ))}
    </div>
  );
}

export default AlignmentGuides;
