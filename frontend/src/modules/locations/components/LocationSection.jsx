import React from 'react';

const LocationSection = ({ icon: Icon, title, subtitle, actions, children }) => (
    <section className="relative bg-card border border-border rounded-lg">
        <div className="flex flex-col gap-3 border-b border-border px-5 py-4 md:flex-row md:items-center md:justify-between">
            <div className="flex items-start gap-3 min-w-0">
                {Icon && (
                    <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                        <Icon size={18} />
                    </div>
                )}
                <div className="min-w-0">
                    <h2 className="text-base font-semibold text-text-primary">{title}</h2>
                    {subtitle && <p className="mt-1 text-sm text-text-secondary">{subtitle}</p>}
                </div>
            </div>
            {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
        </div>
        <div className="p-5">{children}</div>
    </section>
);

export default LocationSection;
