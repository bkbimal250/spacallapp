import React from 'react';

const WebsiteFormPreview = ({ form = {} }) => {
    const style = {
        backgroundColor: form.background_color || '#ffffff',
        color: form.text_color || '#111111',
        borderRadius: form.border_radius || '16px',
        fontFamily: form.font_family || 'Inter',
        borderColor: form.primary_color || '#BD9B5F',
    };

    return (
        <div className="rounded-xl border border-border bg-card p-4">
            <div className="mx-auto max-w-md border p-5 shadow-sm" style={style}>
                <h3 className="mb-4 text-lg font-semibold" style={{ color: form.primary_color || '#BD9B5F' }}>
                    {form.form_title || 'Book Appointment'}
                </h3>
                {['Name', 'Phone', 'Address'].map((label) => (
                    <label key={label} className="mb-3 block text-sm font-medium">
                        {label}
                        <input readOnly maxLength={label === 'Address' ? 20 : undefined} className="mt-1 w-full rounded-lg border border-border bg-white px-3 py-2 text-sm text-gray-700" value="" />
                    </label>
                ))}
                <label className="mb-4 block text-sm font-medium">
                    Notes
                    <input readOnly maxLength={20} className="mt-1 w-full rounded-lg border border-border bg-white px-3 py-2 text-sm text-gray-700" value="" />
                </label>
                <button type="button" className="w-full rounded-lg px-4 py-2 text-sm font-semibold text-white" style={{ backgroundColor: form.button_color || '#25D366' }}>
                    {form.submit_button_text || 'Submit'}
                </button>
            </div>
        </div>
    );
};

export default WebsiteFormPreview;
