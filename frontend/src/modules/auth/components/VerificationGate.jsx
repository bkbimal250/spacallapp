import React, { useState } from 'react';
import SecurityCard from './SecurityCard';

const securityLines = [
    'Keeping staff access protected.',
    'A quick check before your workspace opens.',
    'Small step, safer CRM access.',
];

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const generateId = () => {
    if (window.crypto?.randomUUID) return window.crypto.randomUUID();
    return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
};

const generateChallenge = () => {
    const first = Math.floor(Math.random() * 10) + 1;
    const second = Math.floor(Math.random() * 10) + 1;
    const operator = Math.random() > 0.5 ? '+' : '-';

    if (operator === '-') {
        const left = Math.max(first, second);
        const right = Math.min(first, second);

        return {
            id: generateId(),
            left,
            right,
            operator,
            answer: left - right,
        };
    }

    return {
        id: generateId(),
        left: first,
        right: second,
        operator,
        answer: first + second,
    };
};

const VerificationGate = ({ children }) => {
    const [challenge, setChallenge] = useState(() => generateChallenge());
    const [answer, setAnswer] = useState('');
    const [error, setError] = useState('');
    const [isChecking, setIsChecking] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);
    const [isVerified, setIsVerified] = useState(false);
    const [securityLine] = useState(() => securityLines[Math.floor(Math.random() * securityLines.length)]);

    const refreshChallenge = () => {
        setChallenge(generateChallenge());
        setAnswer('');
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!answer.trim() || isChecking || isSuccess) return;

        setIsChecking(true);
        setError('');

        const isCorrect = Number(answer) === challenge.answer;

        if (!isCorrect) {
            await wait(700);
            setError('That answer was not correct. Try the new question.');
            refreshChallenge();
            setIsChecking(false);
            return;
        }

        await wait(450);
        setIsSuccess(true);
        await wait(650);
        setIsVerified(true);
    };

    if (isVerified) {
        return (
            <div className="flex w-full justify-center animate-auth-fade">
                {children}
            </div>
        );
    }

    const visibleChallenge = {
        id: challenge.id,
        left: challenge.left,
        right: challenge.right,
        operator: challenge.operator,
    };

    return (
        <div className="flex min-h-[100svh] w-full items-center justify-center px-4 py-6">
            <div className="flex w-full flex-col items-center gap-4">
                <SecurityCard
                    challenge={visibleChallenge}
                    answer={answer}
                    error={error}
                    isChecking={isChecking}
                    isSuccess={isSuccess}
                    onAnswerChange={(value) => {
                        setAnswer(value);
                        if (error) setError('');
                    }}
                    onSubmit={handleSubmit}
                />

                <p className="text-center text-xs font-medium text-text-muted">
                    {securityLine}
                </p>
            </div>
        </div>
    );
};

export default VerificationGate;
