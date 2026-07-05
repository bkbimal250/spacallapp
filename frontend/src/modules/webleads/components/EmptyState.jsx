import React from 'react';
import { Inbox } from 'lucide-react';

const EmptyState = ({ title = 'No records found', message = 'Try changing filters or create a new item.' }) => (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card p-10 text-center">
        <Inbox className="mb-3 text-text-muted" size={32} />
        <h3 className="text-base font-semibold text-text-primary">{title}</h3>
        <p className="mt-1 max-w-md text-sm text-text-secondary">{message}</p>
    </div>
);

export default EmptyState;
