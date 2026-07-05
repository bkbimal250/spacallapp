import React from 'react';

const LoadingState = ({ label = 'Loading website leads...' }) => (
    <div className="p-12 text-center text-text-secondary">
        <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-b-2 border-primary" />
        {label}
    </div>
);

export default LoadingState;
