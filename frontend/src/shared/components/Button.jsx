import React from 'react';
import clsx from 'clsx';

const Button = ({ children, variant = 'primary', size = 'md', className, ...props }) => {

    const base =
        'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-150 focus:outline-none';

    const sizes = {
        sm: 'px-3 py-1.5 text-sm',
        md: 'px-4 py-2 text-sm',
        lg: 'px-6 py-2.5 text-base'
    };

    const variants = {

        primary:
            'bg-primary text-white hover:bg-primary-hover',

        secondary:
            'bg-card text-text-primary border border-border hover:bg-background',

        danger:
            'bg-danger text-white hover:bg-danger/90',

        outline:
            'border border-border text-text-primary hover:bg-background',

        ghost:
            'text-text-secondary hover:bg-background'

    };

    return (
        <button
            className={clsx(base, sizes[size], variants[variant], className)}
            {...props}
        >
            {children}
        </button>
    );
};

export default Button;