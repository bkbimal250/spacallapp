import React from 'react';

const Footer = () => {
    return (
        <footer className="bg-sidebar border-t border-border px-6 py-3 text-center text-text-secondary text-sm">
            © {new Date().getFullYear()} CallLog System. All rights reserved.
        </footer>
    );
};

export default Footer;