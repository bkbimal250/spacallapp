import React from 'react';

const Navbar = () => {
    return (
        <header className="bg-white shadow-sm h-16 flex justify-between items-center px-6">
            <div className="text-gray-500">
                {/* Breadcrumbs or Page Title could go here */}
                Dashboard
            </div>
            <div className="flex items-center space-x-4">
                <button className="text-gray-500 hover:text-gray-700">Notifications</button>
                <div className="h-8 w-8 rounded-full bg-gray-300"></div>
            </div>
        </header>
    );
};

export default Navbar;
