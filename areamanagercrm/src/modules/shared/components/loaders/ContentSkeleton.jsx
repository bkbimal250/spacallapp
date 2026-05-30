import React from 'react';
import ContentLoader from 'react-content-loader';

const ContentSkeleton = ({ rows = 5, columns = 4 }) => {
  return (
    <div className="w-full bg-card rounded-xl p-4 animate-in">
      <ContentLoader
        speed={2}
        width="100%"
        height={rows * 60 + 40}
        viewBox={`0 0 1000 ${rows * 60 + 40}`}
        backgroundColor="#f1f5f9"
        foregroundColor="#e2e8f0"
      >
        {/* Table Header */}
        <rect x="20" y="10" rx="4" ry="4" width="960" height="30" />
        
        {/* Table Rows */}
        {Array.from({ length: rows }).map((_, i) => (
          <React.Fragment key={i}>
            <rect x="20" y={60 + i * 60} rx="4" ry="4" width="150" height="25" />
            <rect x="200" y={60 + i * 60} rx="4" ry="4" width="200" height="25" />
            <rect x="430" y={60 + i * 60} rx="4" ry="4" width="250" height="25" />
            <rect x="710" y={60 + i * 60} rx="4" ry="4" width="100" height="25" />
            <rect x="840" y={60 + i * 60} rx="4" ry="4" width="140" height="25" />
          </React.Fragment>      
        ))}
      </ContentLoader>
    </div>
  );
};

export default ContentSkeleton;
