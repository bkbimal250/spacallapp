import React from 'react';

const Footer = () => {
    return (
        <footer className="bg-white border-t p-4 text-center text-gray-600 text-sm">
            &copy; {new Date().getFullYear()} CallLog System. All rights reserved.
        </footer>
    );
};

export default Footer;
