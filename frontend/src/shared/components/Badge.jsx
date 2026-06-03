import React, { memo } from 'react';
import clsx from 'clsx';

const Badge = ({ children, variant = 'gray', className }) => {
    const variants = {
        gray: 'bg-gray-100 text-gray-800',
        red: 'bg-red-100 text-red-800',
        yellow: 'bg-yellow-100 text-yellow-800',
        green: 'bg-green-100 text-green-800',
        blue: 'bg-blue-100 text-blue-800',
        indigo: 'bg-indigo-100 text-indigo-800',
        purple: 'bg-purple-100 text-purple-800',
        pink: 'bg-pink-100 text-pink-800',
        success: 'bg-success/10 text-success border border-success/20',
        danger: 'bg-danger/10 text-danger border border-danger/20',
        warning: 'bg-warning/10 text-warning border border-warning/20',
        info: 'bg-info/10 text-info border border-info/20',
    };

    return (
        <span className={clsx(
            'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
            variants[variant],
            className
        )}>
            {children}
        </span>
    );
};

export default memo(Badge);
