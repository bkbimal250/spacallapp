import React, { memo } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const Pagination = ({ currentPage, totalPages, onPageChange }) => {

    if (totalPages <= 1) return null;

    const getPageNumbers = () => {

        const pages = [];
        const maxVisiblePages = 10;

        let start = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
        let end = Math.min(totalPages, start + maxVisiblePages - 1);

        if (end - start + 1 < maxVisiblePages) {
            start = Math.max(1, end - maxVisiblePages + 1);
        }

        for (let i = start; i <= end; i++) {
            pages.push(i);
        }

        return pages;

    };

    return (

        <div className="bg-card border-t border-border px-4 py-4 flex items-center justify-between">

            {/* MOBILE */}
            <div className="flex-1 flex justify-between sm:hidden">

                <button
                    onClick={() => onPageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="px-4 py-2 rounded-lg border border-border bg-background text-text-primary hover:bg-background/80 disabled:opacity-50"
                >
                    Previous
                </button>

                <button
                    onClick={() => onPageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="px-4 py-2 rounded-lg border border-border bg-background text-text-primary hover:bg-background/80 disabled:opacity-50"
                >
                    Next
                </button>

            </div>

            {/* DESKTOP */}
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">

                {/* PAGE INFO */}
                <p className="text-sm text-text-secondary">

                    Showing page
                    <span className="font-semibold text-primary mx-1">
                        {currentPage}
                    </span>

                    of

                    <span className="font-semibold text-text-primary ml-1">
                        {totalPages}
                    </span>

                </p>

                {/* PAGE BUTTONS */}
                <nav className="inline-flex rounded-lg border border-border overflow-hidden">

                    {/* PREVIOUS */}
                    <button
                        onClick={() => onPageChange(currentPage - 1)}
                        disabled={currentPage === 1}
                        className="px-3 py-2 bg-background text-text-secondary hover:bg-background/70 disabled:opacity-40"
                    >

                        <ChevronLeft className="h-5 w-5" />

                    </button>

                    {/* PAGE NUMBERS */}
                    {getPageNumbers().map(number => (

                        <button
                            key={number}
                            onClick={() => onPageChange(number)}
                            className={`px-4 py-2 text-sm font-medium transition ${currentPage === number
                                    ? 'bg-primary text-white'
                                    : 'bg-background text-text-secondary hover:bg-background/70'
                                }`}
                        >

                            {number}

                        </button>

                    ))}

                    {/* NEXT */}
                    <button
                        onClick={() => onPageChange(currentPage + 1)}
                        disabled={currentPage === totalPages}
                        className="px-3 py-2 bg-background text-text-secondary hover:bg-background/70 disabled:opacity-40"
                    >

                        <ChevronRight className="h-5 w-5" />

                    </button>

                </nav>

            </div>

        </div>

    );

};

export default memo(Pagination);