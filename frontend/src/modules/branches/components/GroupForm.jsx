import React, { useState, useEffect } from 'react';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import Modal from '../../../shared/components/Modal';

const GroupForm = ({ isOpen, onClose, onSubmit, initialData, saving = false }) => {
    const [formData, setFormData] = useState({
        name: '',
        is_active: true,
    });

    useEffect(() => {
        if (initialData) {
            setFormData({
                name: initialData.name || '',
                is_active: initialData.is_active !== undefined ? initialData.is_active : true,
            });
        } else {
            setFormData({
                name: '',
                is_active: true,
            });
        }
    }, [initialData, isOpen]);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        onSubmit(formData);
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={initialData ? 'Edit Branch Group' : 'Create Branch Group'}
        >
            <form onSubmit={handleSubmit} className="space-y-4">
                <Input
                    label="Group Name"
                    name="name"
                    placeholder="e.g. North Zone, Premium Spas"
                    value={formData.name}
                    onChange={handleChange}
                    required
                />

                <div className="flex items-center">
                    <input
                        type="checkbox"
                        id="group_is_active"
                        name="is_active"
                        checked={formData.is_active}
                        onChange={handleChange}
                        className="h-4 w-4 rounded border-border bg-background text-primary focus:ring-primary"
                    />
                    <label
                        htmlFor="group_is_active"
                        className="ml-2 text-sm text-text-primary"
                    >
                        Is Active
                    </label>
                </div>

                <div className="flex justify-end gap-2 pt-4">
                    <Button
                        variant="secondary"
                        onClick={onClose}
                        type="button"
                        disabled={saving}
                    >
                        Cancel
                    </Button>
                    <Button type="submit" loading={saving}>
                        {initialData ? 'Update' : 'Create'}
                    </Button>
                </div>
            </form>
        </Modal>
    );
};

export default GroupForm;
