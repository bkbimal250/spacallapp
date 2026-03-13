import React, { useState, useRef, useEffect } from 'react';
import { Search, ChevronDown, X } from 'lucide-react';

const SearchableSelect = ({
    options,
    value,
    onChange,
    placeholder = "Select option...",
    label,
    className
}) => {

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

    }, []);

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

            {label && (
                <label className="block text-xs font-semibold text-text-secondary mb-1 ml-1 uppercase tracking-wider">
                    {label}
                </label>
            )}

            {/* SELECT BOX */}
            <div
                className={`relative w-full cursor-pointer bg-background border border-border rounded-lg py-2.5 pl-4 pr-10 text-left transition ${isOpen
                    ? 'border-primary ring-2 ring-primary/20'
                    : 'hover:border-border/80'
                    }`}
                onClick={() => setIsOpen(!isOpen)}
            >

                <span
                    className={`block truncate text-sm ${!selectedOption ? 'text-text-muted' : 'text-text-primary font-medium'
                        }`}
                >
                    {selectedOption ? selectedOption.label : placeholder}
                </span>

                {/* ARROW */}
                <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
                    <ChevronDown
                        className={`h-4 w-4 text-text-secondary transition-transform ${isOpen ? 'rotate-180 text-primary' : ''
                            }`}
                    />
                </span>

                {/* CLEAR BUTTON */}
                {value && (
                    <button
                        onClick={clearSelection}
                        className="absolute inset-y-0 right-8 flex items-center group"
                    >
                        <X className="h-4 w-4 text-text-muted group-hover:text-danger transition-colors" />
                    </button>
                )}

            </div>

            {/* DROPDOWN */}
            {isOpen && (

                <div className="absolute z-30 mt-2 max-h-60 w-full overflow-hidden rounded-lg bg-card border border-border shadow-xl">

                    {/* SEARCH */}
                    <div className="sticky top-0 z-10 bg-background px-3 py-2 border-b border-border">

                        <div className="relative">

                            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-text-muted" />

                            <input
                                type="text"
                                className="w-full rounded-md border border-border bg-background pl-8 pr-3 py-1.5 text-sm text-text-primary focus:border-primary focus:ring-1 focus:ring-primary placeholder:text-text-muted"
                                placeholder="Search..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                onClick={(e) => e.stopPropagation()}
                                autoFocus
                            />

                        </div>

                    </div>

                    {/* OPTIONS */}
                    <div className="overflow-auto max-h-[220px]">

                        <div
                            className="cursor-pointer py-2.5 pl-4 pr-9 text-text-secondary hover:bg-background transition border-b border-border"
                            onClick={() => handleSelect({ value: '', label: '' })}
                        >
                            None / All
                        </div>

                        {filteredOptions.length === 0 ? (

                            <div className="py-8 px-4 text-text-muted italic text-center text-sm">
                                No results for "{searchTerm}"
                            </div>

                        ) : (

                            filteredOptions.map(option => (

                                <div
                                    key={option.value}
                                    className={`cursor-pointer py-2.5 pl-4 pr-9 transition ${value === option.value
                                        ? 'bg-primary text-white'
                                        : 'text-text-primary hover:bg-background'
                                        }`}
                                    onClick={() => handleSelect(option)}
                                >

                                    <span className="block truncate font-medium">
                                        {option.label}
                                    </span>

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