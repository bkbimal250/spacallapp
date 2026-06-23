import React, { useState } from 'react';
import { Save } from 'lucide-react';
import Button from '../../../shared/components/Button';
import Input from '../../../shared/components/Input';

const QuickCreateForm = ({ fields, submitLabel = 'Save', loading, disabled, onSubmit }) => {
    const initial = fields.reduce((acc, field) => ({ ...acc, [field.name]: field.defaultValue || '' }), {});
    const [form, setForm] = useState(initial);

    const handleSubmit = async (event) => {
        event.preventDefault();
        await onSubmit(form);
        setForm(initial);
    };

    return (
        <form onSubmit={handleSubmit} className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {fields.map((field) => (
                <Input
                    key={field.name}
                    label={field.label}
                    name={field.name}
                    value={form[field.name] || ''}
                    onChange={(event) => setForm((prev) => ({ ...prev, [field.name]: event.target.value }))}
                    placeholder={field.placeholder}
                    disabled={disabled || loading || field.disabled}
                    required={field.required}
                />
            ))}
            <div className="flex items-end">
                <Button type="submit" loading={loading} disabled={disabled} className="gap-2">
                    <Save size={16} />
                    {submitLabel}
                </Button>
            </div>
        </form>
    );
};

export default QuickCreateForm;
