import React, { useState } from 'react';
import { Check, Copy } from 'lucide-react';

const CopyButton = ({ value, label = 'Copy', copiedLabel = 'Copied', className = '' }) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        if (!value) return;
        await navigator.clipboard.writeText(value);
        setCopied(true);
        window.setTimeout(() => setCopied(false), 1400);
    };

    return (
        <button
            type="button"
            onClick={handleCopy}
            className={`inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-semibold text-text-secondary transition hover:bg-background hover:text-primary ${className}`}
            title={label}
        >
            {copied ? <Check size={14} /> : <Copy size={14} />}
            {copied ? copiedLabel : label}
        </button>
    );
};

export default CopyButton;
