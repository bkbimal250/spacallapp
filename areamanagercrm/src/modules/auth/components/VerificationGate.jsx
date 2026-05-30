import React, { useState, useEffect, useRef } from 'react';

const secureQuotes = [
    "Access verified by system security shield.",
    "Authorized field manager entry path.",
    "Securing device environment parameters...",
    "Temporary field verification active.",
    "Connection authenticated via local check."
];

const VerificationGate = ({ onSuccess }) => {
    const [challenge, setChallenge] = useState({ num1: 0, num2: 0, operator: '+' });
    const [userAnswer, setUserAnswer] = useState('');
    const [status, setStatus] = useState('idle'); // 'idle' | 'checking' | 'error' | 'success'
    const [shake, setShake] = useState(false);
    const [quote, setQuote] = useState('');
    
    // Store correct answer secretly in memory, avoiding any DOM lookup access
    const answerRef = useRef(0);
    const inputRef = useRef(null);

    const generateQuestion = () => {
        const n1 = Math.floor(Math.random() * 10) + 1;
        const n2 = Math.floor(Math.random() * 10) + 1;
        const ops = ['+', '-'];
        const op = ops[Math.floor(Math.random() * ops.length)];

        let finalNum1 = n1;
        let finalNum2 = n2;
        let answer = 0;

        if (op === '-') {
            // Guarantee positive or zero answer for field managers
            if (n1 < n2) {
                finalNum1 = n2;
                finalNum2 = n1;
            }
            answer = finalNum1 - finalNum2;
        } else {
            answer = finalNum1 + finalNum2;
        }

        answerRef.current = answer;
        setChallenge({ num1: finalNum1, num2: finalNum2, operator: op });
        setUserAnswer('');
        
        // Auto-focus input on render or recalculation
        setTimeout(() => {
            if (inputRef.current) {
                inputRef.current.focus();
            }
        }, 50);
    };

    // Initialize challenge and picking a random security quote
    useEffect(() => {
        generateQuestion();
        const randQuote = secureQuotes[Math.floor(Math.random() * secureQuotes.length)];
        setQuote(randQuote);
    }, []);

    const handleSubmit = (e) => {
        e.preventDefault();
        
        // Prevent double submit/spam clicking
        if (status === 'checking' || status === 'success' || !userAnswer.trim()) return;

        setStatus('checking');

        const parsedAnswer = parseInt(userAnswer, 10);
        
        if (parsedAnswer === answerRef.current) {
            setStatus('success');
            // Trigger transition after showing animated success badge
            setTimeout(() => {
                onSuccess();
            }, 1000);
        } else {
            // Trigger physical error feedback (shake)
            setShake(true);
            setStatus('error');
            
            // Wait for shake animation to finish, then reset input and generate new question
            setTimeout(() => {
                setShake(false);
                setStatus('idle');
                generateQuestion();
            }, 800);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-background px-4 py-8 select-none">
            <div 
                className={`relative w-full max-w-sm rounded-2xl border border-border bg-card p-6 shadow-xl transition-all duration-300 ${
                    shake ? 'animate-shake border-danger/60' : 'border-border'
                } ${status === 'success' ? 'animate-success-pulse border-success/40' : ''}`}
            >
                {/* Shield Header */}
                <div className="flex flex-col items-center text-center">
                    <div className={`p-3 rounded-full mb-4 transition-all duration-300 ${
                        status === 'success' ? 'bg-success/15 text-success' :
                        status === 'error' ? 'bg-danger/15 text-danger animate-pulse' :
                        'bg-primary/10 text-primary'
                    }`}>
                        {status === 'success' ? (
                            <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                            </svg>
                        ) : (
                            <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                            </svg>
                        )}
                    </div>
                    
                    <span className="text-[10px] font-bold uppercase tracking-wider text-primary bg-primarySoft px-2.5 py-1 rounded-full mb-2">
                        System Gate
                    </span>
                    <h2 className="text-xl font-bold tracking-tight text-textPrimary">
                        Security Verification
                    </h2>
                    <p className="mt-1.5 text-xs text-textSecondary px-2">
                        Solve this quick challenge to access the CRM portal securely.
                    </p>
                </div>

                {/* Question and Challenge Block */}
                <form onSubmit={handleSubmit} className="mt-6 space-y-5">
                    <div className="flex flex-col items-center justify-center bg-background/60 border border-border/80 rounded-2xl py-5 px-6">
                        <span className="text-[10px] font-bold uppercase tracking-widest text-textSecondary mb-2">Solve Math Challenge</span>
                        <div className="flex items-center gap-3 text-3xl font-extrabold text-textPrimary tracking-wider select-none font-mono">
                            <span>{challenge.num1}</span>
                            <span className="text-primary">{challenge.operator}</span>
                            <span>{challenge.num2}</span>
                            <span className="text-textSecondary">=</span>
                            <span className="text-primary animate-pulse">?</span>
                        </div>
                    </div>

                    {/* Numeric Mobile-Friendly Input */}
                    <div className="relative">
                        <input
                            ref={inputRef}
                            type="number"
                            pattern="[0-9]*"
                            inputMode="numeric"
                            value={userAnswer}
                            disabled={status === 'checking' || status === 'success'}
                            onChange={(e) => setUserAnswer(e.target.value)}
                            placeholder="Enter solution"
                            className={`w-full text-center text-xl font-bold tracking-wide h-12 rounded-xl border bg-background px-4 text-textPrimary outline-none transition-all focus:ring-2 focus:ring-primary/20 ${
                                status === 'error' ? 'border-danger focus:border-danger' : 
                                status === 'success' ? 'border-success focus:border-success' :
                                'border-border focus:border-primary'
                            }`}
                        />
                    </div>

                    {/* Action Button */}
                    <button
                        type="submit"
                        disabled={status === 'checking' || status === 'success' || !userAnswer.trim()}
                        className={`w-full h-11 rounded-xl text-sm font-semibold text-white flex items-center justify-center gap-2 transition-all duration-200 active:scale-[0.98] ${
                            status === 'success'
                                ? 'bg-success hover:bg-success'
                                : 'bg-primary hover:bg-primary/95 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm'
                        }`}
                    >
                        {status === 'checking' && (
                            <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                            </svg>
                        )}
                        {status === 'success' ? 'Verified Successfully' : 'Continue Securely'}
                    </button>
                </form>

                {/* Footer Security Badging & Quotes */}
                <div className="mt-6 pt-5 border-t border-border/60 text-center space-y-2">
                    <p className="text-[10px] text-textMuted font-medium italic min-h-[16px] px-2 truncate">
                        {quote}
                    </p>
                    <div className="flex items-center justify-center gap-1.5 text-success/80 text-[10px] font-bold select-none uppercase tracking-wider">
                        <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M2.166 4.9L10 1.154l7.834 3.746A2 2 0 0119 6.753v5.228a9 9 0 01-5.186 8.16l-3.5 1.677a.75.75 0 01-.628 0l-3.5-1.677A9 9 0 011 11.981V6.753c0-.77.447-1.47 1.166-1.853zM10 4.2a.75.75 0 01.75.75v5.5a.75.75 0 01-1.5 0V5a.75.75 0 01.75-.75zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                        </svg>
                        Authorized Personnel Only
                    </div>
                </div>
            </div>
        </div>
    );
};

export default VerificationGate;
