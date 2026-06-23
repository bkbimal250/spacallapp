import React from 'react';
import clsx from 'clsx';

const Modal = ({ isOpen, onClose, title, children, maxWidth = 'max-w-4xl', hideFooter = false }) => {

    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 z-40 flex items-center justify-center px-2"
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
                className={`relative w-full ${maxWidth} h-[88vh] bg-card border border-border rounded-xl shadow-xl flex flex-col`}
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

                {/* BODY (Scrollable) */}
                <div className="px-6 py-5 text-text-primary overflow-y-auto flex-1">
                    {children}
                </div>

                {/* FOOTER */}
                {!hideFooter && (
                    <div className="px-6 py-4 border-t border-border flex justify-end">
                        <button
                            onClick={onClose}
                            className="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary-hover transition"
                        >
                            Close
                        </button>
                    </div>
                )}

            </div>

        </div>
    );
};

export default Modal;
