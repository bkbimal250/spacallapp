import React from 'react';
import { BarLoader } from 'react-spinners';

const SubtleLoader = ({ color = "#6366f1", height = 2, width = "100%", isVisible = true }) => {
  if (!isVisible) return <div className="h-[2px]" />;
  
  return (
    <div className="w-full h-[2px] overflow-hidden relative opacity-0 animate-in">
      <BarLoader color={color} height={height} width="100%" loading={isVisible} />
    </div>
  );
};

export default SubtleLoader;
