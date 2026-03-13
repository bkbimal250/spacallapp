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

        const cleanedData = {
            ...formData,
            booking_date: formData.booking_date || null,
            remarks: formData.remarks || null,
        };

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
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={initialData ? 'Edit Lead' : 'Create Lead'}
        >
            <form onSubmit={handleSubmit} className="space-y-4 text-text-primary">

                <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">
                        Status
                    </label>

                    <select
                        name="status"
                        value={formData.status}
                        onChange={handleChange}
                        className="w-full px-3 py-2 bg-card border border-border rounded-lg text-text-primary focus:border-primary outline-none"
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
                        className="bg-card border-border text-text-primary"
                    />
                )}

                {['coming', 'interested'].includes(formData.status) && (
                    <div>
                        <label className="block text-sm font-medium text-text-secondary mb-1">
                            Remarks
                        </label>

                        <textarea
                            name="remarks"
                            value={formData.remarks}
                            onChange={handleChange}
                            rows="3"
                            placeholder="Enter lead details or notes..."
                            required={formData.status === 'interested'}
                            className="w-full px-3 py-2 bg-card border border-border rounded-lg text-text-primary focus:border-primary outline-none"
                        />
                    </div>
                )}

                <div className="flex justify-end gap-2 mt-6">

                    <Button
                        variant="outline"
                        onClick={onClose}
                        type="button"
                        className="border-border text-text-secondary"
                    >
                        Cancel
                    </Button>

                    <Button
                        type="submit"
                        className="bg-primary hover:bg-primary-hover text-white"
                    >
                        {initialData ? 'Update' : 'Create'}
                    </Button>

                </div>

            </form>
        </Modal>
    );
};

export default LeadForm;