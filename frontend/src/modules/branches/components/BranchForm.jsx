import React, { useState, useEffect } from 'react';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import Modal from '../../../shared/components/Modal';

const BranchForm = ({ isOpen, onClose, onSubmit, initialData }) => {
    const [formData, setFormData] = useState({
        spa_name: '',
        code: '',
        state: '',
        city: '',
        area: '',
        postal_code: '',
        address: '',
        is_active: true,
    });

    useEffect(() => {
        if (initialData) {
            setFormData({
                spa_name: initialData.spa_name || '',
                code: initialData.code || '',
                state: initialData.state || '',
                city: initialData.city || '',
                area: initialData.area || '',
                postal_code: initialData.postal_code || '',
                address: initialData.address || '',
                is_active: initialData.is_active !== undefined ? initialData.is_active : true,
            });
        } else {
            setFormData({
                spa_name: '',
                code: '',
                state: '',
                city: '',
                area: '',
                postal_code: '',
                address: '',
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
        <Modal isOpen={isOpen} onClose={onClose} title={initialData ? 'Edit Branch' : 'Create Branch'}>
            <form onSubmit={handleSubmit} className="space-y-4">
                <Input
                    label="Spa Name"
                    name="spa_name"
                    value={formData.spa_name}
                    onChange={handleChange}
                    required
                />
                <Input
                    label="Branch Code"
                    name="code"
                    value={formData.code}
                    onChange={handleChange}
                    required
                />
                <div className="grid grid-cols-2 gap-4">
                    <Input
                        label="State"
                        name="state"
                        value={formData.state}
                        onChange={handleChange}
                        required
                    />
                    <Input
                        label="City"
                        name="city"
                        value={formData.city}
                        onChange={handleChange}
                        required
                    />
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <Input
                        label="Area (Optional)"
                        name="area"
                        value={formData.area}
                        onChange={handleChange}
                    />
                    <Input
                        label="Postal Code"
                        name="postal_code"
                        type="number"
                        value={formData.postal_code}
                        onChange={handleChange}
                        required
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Address
                    </label>
                    <textarea
                        name="address"
                        value={formData.address}
                        onChange={handleChange}
                        required
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        rows="3"
                    ></textarea>
                </div>
                <div className="flex items-center">
                    <input
                        type="checkbox"
                        id="is_active"
                        name="is_active"
                        checked={formData.is_active}
                        onChange={handleChange}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
                        Is Active
                    </label>
                </div>
                <div className="flex justify-end space-x-2 mt-6">
                    <Button variant="secondary" onClick={onClose} type="button">
                        Cancel
                    </Button>
                    <Button type="submit">
                        {initialData ? 'Update' : 'Create'}
                    </Button>
                </div>
            </form>
        </Modal>
    );
};

export default BranchForm;
