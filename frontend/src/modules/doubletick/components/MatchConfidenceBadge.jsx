import React from 'react';
import { AlertTriangle, CheckCircle2, Sparkles } from 'lucide-react';

const MatchConfidenceBadge = ({ confidence = 0, compact = false }) => {
    const score = Math.round(Number(confidence || 0) * 100);
    const safe = score >= 92;
    const suggestion = score >= 80 && score < 92;
    const Icon = safe ? CheckCircle2 : suggestion ? Sparkles : AlertTriangle;
    const label = safe ? 'Safe Match' : suggestion ? 'Suggestion Only' : 'Manual Needed';
    const tone = safe
        ? 'bg-success/10 text-success border-success/20'
        : suggestion
            ? 'bg-warning/10 text-warning border-warning/20'
            : 'bg-danger/10 text-danger border-danger/20';

    return (
        <span className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-1 text-xs font-semibold ${tone}`}>
            <Icon size={12} />
            {compact ? `${score}%` : `${label} · ${score}%`}
        </span>
    );
};

export default MatchConfidenceBadge;
