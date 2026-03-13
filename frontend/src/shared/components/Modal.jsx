import React from 'react';
import clsx from 'clsx';

const Modal = ({ isOpen, onClose, title, children }) => {

    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center px-4"
            role="dialog"
            aria-modal="true"
        >

            {/* BACKDROP */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* MODAL */}
            <div
                className="relative w-full max-w-lg bg-card border border-border rounded-xl shadow-xl"
            >

                {/* HEADER */}
                <div className="px-6 py-4 border-b border-border flex items-center justify-between">

                    <h3 className="text-lg font-semibold text-text-primary">
                        {title}
                    </h3>

                    <button
                        onClick={onClose}
                        className="text-text-secondary hover:text-text-primary"
                    >
                        ✕
                    </button>

                </div>

                {/* BODY */}
                <div className="px-6 py-5 text-text-primary">
                    {children}
                </div>

                {/* FOOTER */}
                <div className="px-6 py-4 border-t border-border flex justify-end">

                    <button
                        onClick={onClose}
                        className="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary-hover transition"
                    >
                        Close
                    </button>

                </div>

            </div>

        </div>
    );

};

export default Modal;