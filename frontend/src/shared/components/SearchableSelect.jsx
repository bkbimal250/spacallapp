import React, { useState, useRef, useEffect, useMemo, useCallback, memo } from 'react';
import { Search, ChevronDown, X } from 'lucide-react';

const SearchableSelect = ({
    options,
    value,
    onChange,
    placeholder = "Select option...",
    label,
    className,
    disabled = false,
    allowEmpty = true,
}) => {

    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [activeIndex, setActiveIndex] = useState(0);

    const wrapperRef = useRef(null);
    const inputRef = useRef(null);

    const normalizedValue = value === null || value === undefined ? '' : String(value);
    const selectedOption = options.find(opt => String(opt.value) === normalizedValue);

    useEffect(() => {
        function handleClickOutside(event) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        }

        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const filteredOptions = useMemo(() => {
        const normalizedSearch = searchTerm.toLowerCase();
        return options.filter(opt =>
            `${opt.label || ''} ${opt.title || ''} ${opt.searchText || ''}`
                .toLowerCase()
                .includes(normalizedSearch)
        );
    }, [options, searchTerm]);

    // 🔥 Highlight search text - Optimized
    const highlightedOptions = useMemo(() => {
        if (!searchTerm) return null;
        return searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }, [searchTerm]);

    const highlightText = useCallback((text) => {
        if (!highlightedOptions) return text;

        const parts = text.split(new RegExp(`(${highlightedOptions})`, "gi"));
        
        return parts.map((part, i) =>
            part.toLowerCase() === searchTerm.toLowerCase() ? (
                <span key={i} className="bg-primary/20 text-primary px-0.5 rounded font-bold">
                    {part}
                </span>
            ) : part
        );
    }, [searchTerm, highlightedOptions]);

    const handleSelect = useCallback((option) => {
        onChange(option.value);
        setIsOpen(false);
        setSearchTerm('');
    }, [onChange]);

    const clearSelection = useCallback((e) => {
        e.stopPropagation();
        onChange('');
        setSearchTerm('');
    }, [onChange]);

    // 🔥 Keyboard navigation
    const handleKeyDown = useCallback((e) => {
        if (!isOpen) return;

        if (e.key === "ArrowDown") {
            e.preventDefault();
            setActiveIndex(prev => (prev + 1) % filteredOptions.length);
        }

        if (e.key === "ArrowUp") {
            e.preventDefault();
            setActiveIndex(prev => (prev - 1 + filteredOptions.length) % filteredOptions.length);
        }

        if (e.key === "Enter") {
            e.preventDefault();
            if (filteredOptions[activeIndex]) {
                handleSelect(filteredOptions[activeIndex]);
            }
        }
    }, [isOpen, filteredOptions, activeIndex, handleSelect]);

    return (
        <div className={`relative min-w-0 ${className || ''}`} ref={wrapperRef}>

            {label && (
                <label className="block text-xs font-semibold text-text-secondary mb-1 ml-1 uppercase tracking-wider">
                    {label}
                </label>
            )}

            {/* SELECT BOX */}
            <div
                className={`relative w-full bg-background border border-border rounded-lg py-2.5 pl-4 pr-10 text-left transition
                ${disabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}
                ${isOpen ? 'border-primary ring-2 ring-primary/20 shadow-md' : disabled ? '' : 'hover:border-border/80'}`}
                onClick={() => {
                    if (disabled) return;
                    setIsOpen(!isOpen);
                    setTimeout(() => inputRef.current?.focus(), 100);
                }}
            >

                <span className="block min-w-0">
                    <span className={`block truncate text-sm ${!selectedOption ? 'text-text-muted' : 'text-text-primary font-medium'}`}>
                        {selectedOption ? selectedOption.label : placeholder}
                    </span>
                    {selectedOption?.description && (
                        <span className="mt-0.5 block truncate text-[11px] text-text-secondary">
                            {selectedOption.description}
                        </span>
                    )}
                </span>

                {/* ARROW */}
                <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
                    <ChevronDown
                        className={`h-4 w-4 text-text-secondary transition-transform ${isOpen ? 'rotate-180 text-primary' : ''}`}
                    />
                </span>

                {/* CLEAR BUTTON */}
                {normalizedValue && !disabled && (
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
                <div className="absolute z-[9999] mt-2.5 w-full min-w-[280px] rounded-xl bg-card border border-border shadow-2xl overflow-hidden animate-fadeIn backdrop-blur-sm">

                    {/* SEARCH */}
                    <div className="sticky top-0 bg-background px-3 py-2 border-b border-border">
                        <div className="relative">
                            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-text-muted" />

                            <input
                                ref={inputRef}
                                type="text"
                                className="w-full rounded-md border border-border bg-background pl-8 pr-3 py-1.5 text-sm focus:border-primary focus:ring-1 focus:ring-primary"
                                placeholder="Search..."
                                value={searchTerm}
                                onChange={(e) => {
                                    setSearchTerm(e.target.value);
                                    setActiveIndex(0);
                                }}
                                onKeyDown={handleKeyDown}
                                onClick={(e) => e.stopPropagation()}
                                autoFocus
                            />
                        </div>
                    </div>

                    {/* OPTIONS */}
                    <div className="max-h-60 overflow-y-auto">

                        {/* NONE OPTION */}
                        {allowEmpty && (
                            <div
                                className="cursor-pointer py-2.5 pl-4 pr-9 text-text-secondary hover:bg-background border-b border-border"
                                onClick={() => handleSelect({ value: '', label: '' })}
                            >
                                None / All
                            </div>
                        )}

                        {filteredOptions.length === 0 ? (
                            <div className="py-8 px-4 text-text-muted italic text-center text-sm">
                                No results for "{searchTerm}"
                            </div>
                        ) : (
                            filteredOptions.map((option, index) => (
                                <div
                                    key={option.value}
                                    className={`cursor-pointer py-2.5 pl-4 pr-9 transition-all
                                    ${normalizedValue === String(option.value)
                                            ? 'bg-primary text-white'
                                            : index === activeIndex
                                                ? 'bg-primary/10'
                                                : 'hover:bg-background'
                                        }`}
                                    onClick={() => handleSelect(option)}
                                >
                                    <span className="block truncate font-medium">
                                        {highlightText(option.label)}
                                    </span>
                                    {option.description && (
                                        <span className={`mt-0.5 block text-xs whitespace-normal break-words ${
                                            normalizedValue === String(option.value) ? 'text-white/80' : 'text-text-secondary'
                                        }`}>
                                            {highlightText(option.description)}
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

export default memo(SearchableSelect);
