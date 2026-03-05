import React, { useState, useEffect } from 'react';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import Modal from '../../../shared/components/Modal';
const LeadForm = ({ isOpen, onClose, onSubmit, initialData }) => {
    const [formData, setFormData] = useState({
        status: 'pending',
        booking_date: '',
        remarks: '',
    });

    useEffect(() => {
        // Form initialization logic if needed
    }, [isOpen]);

    useEffect(() => {
        if (initialData) {
            setFormData({
                status: initialData.status || 'pending',
                booking_date: initialData.booking_date || '',
                remarks: initialData.remarks || '',
            });
        } else {
            setFormData({
                status: 'pending',
                booking_date: '',
                remarks: '',
            });
        }
    }, [initialData, isOpen]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();

        // Clean data: convert empty strings to null for the API
        const cleanedData = {
            ...formData,
            booking_date: formData.booking_date || null,
            remarks: formData.remarks || null,
        };

        // Only send fields relevant to the current status to skip server-side clearing issues
        const finalData = { status: formData.status };
        if (['coming', 'interested'].includes(formData.status)) {
            finalData.booking_date = cleanedData.booking_date;
            finalData.remarks = cleanedData.remarks;
        } else {
            finalData.booking_date = null;
        }

        onSubmit(finalData);
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={initialData ? 'Edit Lead' : 'Create Lead'}>
            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                    <select
                        name="status"
                        value={formData.status}
                        onChange={handleChange}
                        className="w-full border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    >
                        <option value="pending">Pending</option>
                        <option value="ringing">Ringing</option>
                        <option value="coming">Coming</option>
                        <option value="interested">Interested</option>
                        <option value="not_interested">Not Interested</option>
                    </select>
                </div>

                {['coming', 'interested'].includes(formData.status) && (
                    <Input
                        label="Booking Date"
                        name="booking_date"
                        type="date"
                        value={formData.booking_date}
                        onChange={handleChange}
                        required
                    />
                )}

                {['coming', 'interested'].includes(formData.status) && (
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Remarks</label>
                        <textarea
                            name="remarks"
                            value={formData.remarks}
                            onChange={handleChange}
                            rows="3"
                            className="w-full border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            placeholder="Enter lead details or notes..."
                            required={formData.status === 'interested'}
                        ></textarea>
                    </div>
                )}

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

export default LeadForm;
