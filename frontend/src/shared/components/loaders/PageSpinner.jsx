import React from 'react';
import { GridLoader } from 'react-spinners';

const PageSpinner = ({ message = "Loading data...", color = "#6366f1" }) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 space-y-4 animate-in">
      <GridLoader color={color} size={15} margin={2} />
      {message && (
        <p className="text-text-secondary font-medium animate-pulse">
          {message}
        </p>
      )}
    </div>
  );
};

export default PageSpinner;
