import React from 'react';
import { PulseLoader } from 'react-spinners';

const ButtonSpinner = ({ color = "#ffffff", size = 8 }) => {
  return (
    <span className="flex items-center justify-center p-1.5 leading-none">
      <PulseLoader color={color} size={size} margin={2} />
    </span>
  );
};

export default ButtonSpinner;
