import React from 'react';
import CopyButton from './CopyButton';

export const buildWidgetCode = (form = {}) => `<div id="mastercall-form"></div>

<script
 src="https://api.mastercall.in/forms/widget.js"
 data-key="${form.form_key || 'FORM_KEY'}"
 data-primary-color="${form.primary_color || '#BD9B5F'}"
 data-button-color="${form.button_color || '#25D366'}"
 data-radius="${form.border_radius || '20'}"
 data-theme="${form.theme || 'dark'}">
</script>`;

export const buildReactExample = (form = {}) => `await fetch("https://api.mastercall.in/api/v1/web-leads/submit/", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    form_key: "${form.form_key || 'FORM_KEY'}",
    name,
    phone,
    address,
    notes,
    submitted_from_url: window.location.href
  })
});`;

const CodeBlock = ({ title, code }) => (
    <div className="rounded-xl border border-border bg-background p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
            <CopyButton value={code} label="Copy" />
        </div>
        <pre className="custom-scrollbar overflow-auto whitespace-pre-wrap rounded-lg bg-card p-3 text-xs text-text-secondary">{code}</pre>
    </div>
);

const WebsiteFormIntegrationCode = ({ form }) => (
    <div className="grid gap-4 lg:grid-cols-2">
        <CodeBlock title="HTML Widget Script" code={buildWidgetCode(form)} />
        <CodeBlock title="React/Next.js API Example" code={buildReactExample(form)} />
    </div>
);

export default WebsiteFormIntegrationCode;
