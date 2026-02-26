import React, { useState, useRef, useEffect } from 'react';
import { Search, ChevronDown, X } from 'lucide-react';

const SearchableSelect = ({ options, value, onChange, placeholder = "Select option...", label, className }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const wrapperRef = useRef(null);

    const selectedOption = options.find(opt => opt.value === value);

    useEffect(() => {
        function handleClickOutside(event) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [wrapperRef]);

    const filteredOptions = options.filter(opt =>
        opt.label.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const handleSelect = (option) => {
        onChange(option.value);
        setIsOpen(false);
        setSearchTerm('');
    };

    const clearSelection = (e) => {
        e.stopPropagation();
        onChange('');
        setSearchTerm('');
    };

    return (
        <div className={`relative ${className}`} ref={wrapperRef}>
            {label && <label className="block text-[11px] font-black text-gray-400 uppercase tracking-wider mb-1.5 ml-1">{label}</label>}
            <div
                className={`relative w-full cursor-pointer bg-gray-50 border-gray-100 rounded-xl py-2.5 pl-4 pr-10 text-left border transition-all duration-200 focus:outline-none ${isOpen ? 'border-indigo-500 ring-2 ring-indigo-500/20 bg-white shadow-sm' : 'hover:border-gray-200 shadow-none'
                    }`}
                onClick={() => setIsOpen(!isOpen)}
            >
                <span className={`block truncate text-sm font-semibold ${!selectedOption ? 'text-gray-400' : 'text-gray-700'}`}>
                    {selectedOption ? selectedOption.label : placeholder}
                </span>
                <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
                    <ChevronDown className={`h-4 w-4 text-gray-400 transition-transform duration-200 ${isOpen ? 'rotate-180 text-indigo-500' : ''}`} aria-hidden="true" />
                </span>
                {value && (
                    <button
                        onClick={clearSelection}
                        className="absolute inset-y-0 right-8 flex items-center group"
                    >
                        <X className="h-4 w-4 text-gray-400 group-hover:text-red-500 transition-colors" />
                    </button>
                )}
            </div>

            {isOpen && (
                <div className="absolute z-20 mt-2 max-h-60 w-full overflow-hidden rounded-xl bg-white text-base shadow-xl ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm animate-in fade-in zoom-in duration-200">
                    <div className="sticky top-0 z-10 bg-gray-50/80 backdrop-blur-md px-3 py-2 border-b border-gray-100">
                        <div className="relative group">
                            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-gray-400 group-focus-within:text-indigo-500 transition-colors" />
                            <input
                                type="text"
                                className="w-full rounded-lg border-gray-200 bg-white pl-8 pr-3 py-1.5 text-xs font-medium focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 border transition-all placeholder:text-gray-400"
                                placeholder="Search..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                onClick={(e) => e.stopPropagation()}
                                autoFocus
                            />
                        </div>
                    </div>
                    <div className="overflow-auto max-h-[220px] custom-scrollbar">
                        <div
                            className="relative cursor-pointer select-none py-2.5 pl-4 pr-9 text-gray-500 hover:bg-indigo-50 hover:text-indigo-700 text-xs font-bold uppercase tracking-tight transition-colors border-b border-gray-50"
                            onClick={() => handleSelect({ value: '', label: '' })}
                        >
                            <span className="block truncate">None / All</span>
                        </div>
                        {filteredOptions.length === 0 ? (
                            <div className="relative cursor-default select-none py-8 px-4 text-gray-400 italic text-center text-xs">
                                <div className="mb-2 text-2xl font-normal">🔍</div>
                                No branches found matching "{searchTerm}"
                            </div>
                        ) : (
                            filteredOptions.map((option) => (
                                <div
                                    key={option.value}
                                    className={`relative cursor-pointer select-none py-2.5 pl-4 pr-9 transition-all ${value === option.value ? 'bg-indigo-600 text-white' : 'text-gray-700 hover:bg-indigo-50 hover:text-indigo-700'
                                        }`}
                                    onClick={() => handleSelect(option)}
                                >
                                    <span className={`block truncate ${value === option.value ? 'font-bold' : 'font-semibold text-sm'}`}>
                                        {option.label}
                                    </span>
                                    {value === option.value && (
                                        <span className="absolute inset-y-0 right-0 flex items-center pr-3">
                                            <div className="h-1.5 w-1.5 rounded-full bg-white shadow-sm shadow-indigo-200"></div>
                                        </span>
                                    )}
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default SearchableSelect;

