import React, { useState, useEffect } from 'react';
import Modal from '../../../shared/components/Modal';
import Button from '../../../shared/components/Button';
import Input from '../../../shared/components/Input';

const ContactForm = ({ isOpen, onClose, onSubmit, initialData }) => {

    const [formData, setFormData] = useState({
        name: '',
        phone_number: '',
        email: '',
        city: '',
        country: '',
    });

    const [errors, setErrors] = useState({});

    useEffect(() => {

        if (initialData) {

            setFormData({
                name: initialData.name || '',
                phone_number: initialData.phone_number || '',
                email: initialData.email || '',
                city: initialData.city || '',
                country: initialData.country || '',
            });

        } else {

            setFormData({
                name: '',
                phone_number: '',
                email: '',
                city: '',
                country: '',
            });

        }

        setErrors({});

    }, [initialData, isOpen]);

    const validate = () => {

        const newErrors = {};

        if (!formData.name.trim()) {
            newErrors.name = "Name is required";
        }

        if (!formData.phone_number.trim()) {
            newErrors.phone_number = "Phone number is required";
        }

        setErrors(newErrors);

        return Object.keys(newErrors).length === 0;

    };

    const handleChange = (e) => {

        const { name, value } = e.target;

        setFormData(prev => ({
            ...prev,
            [name]: value
        }));

        if (errors[name]) {
            setErrors(prev => ({
                ...prev,
                [name]: ''
            }));
        }

    };

    const handleSubmit = (e) => {

        e.preventDefault();

        if (validate()) {
            onSubmit(formData);
        }

    };

    return (

        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={initialData ? "Edit Contact" : "Add Contact"}
        >

            <form
                onSubmit={handleSubmit}
                className="space-y-4 py-4"
            >

                <Input
                    label="Name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    placeholder="John Doe"
                    error={errors.name}
                    required
                />

                <Input
                    label="Phone Number"
                    name="phone_number"
                    value={formData.phone_number}
                    onChange={handleChange}
                    placeholder="+1234567890"
                    error={errors.phone_number}
                    required
                />

                <Input
                    label="Email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="john@example.com"
                />

                <div className="grid grid-cols-2 gap-4">

                    <Input
                        label="City"
                        name="city"
                        value={formData.city}
                        onChange={handleChange}
                        placeholder="Mumbai"
                    />

                    <Input
                        label="Country"
                        name="country"
                        value={formData.country}
                        onChange={handleChange}
                        placeholder="India"
                    />

                </div>

                <div className="pt-4 flex justify-end space-x-3">

                    <Button
                        type="button"
                        variant="secondary"
                        onClick={onClose}
                    >
                        Cancel
                    </Button>

                    <Button type="submit">

                        {initialData
                            ? "Save Changes"
                            : "Create Contact"}

                    </Button>

                </div>

            </form>

        </Modal>

    );

};

export default ContactForm;