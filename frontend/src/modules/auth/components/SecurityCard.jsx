import React, { useEffect, useRef } from 'react';
import { Check, Loader2, LockKeyhole, ShieldCheck } from 'lucide-react';

const SecurityCard = ({
    challenge,
    answer,
    error,
    isChecking,
    isSuccess,
    onAnswerChange,
    onSubmit,
}) => {
    const inputRef = useRef(null);
    const canContinue = answer.trim().length > 0 && !isChecking && !isSuccess;

    useEffect(() => {
        inputRef.current?.focus();
    }, [challenge.id]);

    return (
        <form
            onSubmit={onSubmit}
            className={`w-full max-w-md animate-auth-fade rounded-2xl border border-border bg-card p-6 shadow-xl backdrop-blur transition-all duration-300 ${error ? 'animate-security-shake' : ''
                }`}
        >
            <div className="flex flex-col items-center text-center">
                <div className={`mb-4 flex h-14 w-14 items-center justify-center rounded-2xl shadow-lg transition-all duration-300 ${isSuccess
                        ? 'bg-success/20 text-success'
                        : 'bg-primary/20 text-primary'
                    }`}>
                    {isSuccess ? <Check size={28} strokeWidth={3} /> : <ShieldCheck size={28} />}
                </div>

                <div className="mb-3 inline-flex items-center gap-1.5 rounded-full border border-border bg-background px-3 py-1 text-xs font-semibold text-text-secondary">
                    <LockKeyhole size={13} />
                    Secure CRM Access
                </div>

                <h1 className="text-2xl font-bold text-text-primary">
                    Security Verification
                </h1>
                <p className="mt-2 max-w-xs text-sm leading-6 text-text-secondary">
                    Please verify you are human before accessing CRM
                </p>
            </div>

            <div className="mt-6 rounded-2xl border border-border bg-background p-4 text-center">
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-text-muted">
                    Quick check
                </p>
                <div className="mt-2 text-4xl font-bold text-text-primary">
                    {challenge.left} {challenge.operator} {challenge.right} = ?
                </div>
            </div>

            <div className="mt-5 flex flex-col gap-4">
                <label className="sr-only" htmlFor="security-answer">
                    Security answer
                </label>
                <input
                    ref={inputRef}
                    id="security-answer"
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    autoComplete="off"
                    value={answer}
                    disabled={isChecking || isSuccess}
                    onChange={(e) => onAnswerChange(e.target.value.replace(/\D/g, '').slice(0, 2))}
                    placeholder="Enter answer"
                    className="min-h-14 w-full rounded-2xl border border-border bg-background px-4 text-center text-2xl font-semibold text-text-primary shadow-sm outline-none transition-all duration-300 placeholder:text-base placeholder:font-medium placeholder:text-text-muted focus:ring-2 focus:ring-primary/30 disabled:cursor-not-allowed disabled:opacity-70"
                />

                {error && (
                    <p className="rounded-xl border border-danger/30 bg-danger/10 px-3 py-2 text-center text-sm font-medium text-danger">
                        {error}
                    </p>
                )}

                <button
                    type="submit"
                    disabled={!canContinue}
                    className="flex min-h-12 w-full items-center justify-center gap-2 rounded-2xl bg-primary px-4 py-3 text-base font-semibold text-white shadow-lg transition-all duration-300 hover:bg-primary-hover active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
                >
                    {isChecking && <Loader2 size={18} className="animate-spin" />}
                    {isSuccess && <Check size={18} />}
                    {isSuccess ? 'Verified' : isChecking ? 'Checking...' : 'Continue Securely'}
                </button>
            </div>

            <p className="mt-5 text-center text-xs leading-5 text-text-muted">
                Protected access for authorized staff only
            </p>
        </form>
    );
};

export default SecurityCard;
