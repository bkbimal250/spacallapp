import React, { forwardRef } from 'react';
import clsx from 'clsx';

const Input = forwardRef(({ label, error, className, ...props }, ref) => {

    return (
        <div className={className}>

            {label && (
                <label className="block text-sm font-medium text-text-secondary mb-1">
                    {label}
                </label>
            )}

            <input
                ref={ref}
                className={clsx(
                    'block w-full px-3 py-2 rounded-lg border border-border bg-background text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary text-sm transition',
                    error && 'border-danger text-danger placeholder:text-danger focus:ring-danger focus:border-danger'
                )}
                {...props}
            />

            {error && (
                <p className="mt-1 text-xs text-danger">
                    {error}
                </p>
            )}

        </div>
    );

});

Input.displayName = 'Input';

export default Input;