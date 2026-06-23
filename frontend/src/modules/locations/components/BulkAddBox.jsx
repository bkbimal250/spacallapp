import React, { useState } from 'react';
import { Plus } from 'lucide-react';
import Button from '../../../shared/components/Button';
import { linesToNames } from '../utils';

const BulkAddBox = ({ label, placeholder, disabled, loading, onSubmit }) => {
    const [value, setValue] = useState('');

    const handleSubmit = async (event) => {
        event.preventDefault();
        const names = linesToNames(value);
        if (!names.length) return;
        await onSubmit(names);
        setValue('');
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-3">
            <label className="block text-sm font-medium text-text-secondary">{label}</label>
            <textarea
                value={value}
                onChange={(event) => setValue(event.target.value)}
                placeholder={placeholder}
                rows={5}
                disabled={disabled || loading}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <Button type="submit" loading={loading} disabled={disabled || !linesToNames(value).length} className="gap-2">
                <Plus size={16} />
                Add Multiple
            </Button>
        </form>
    );
};

export default BulkAddBox;
