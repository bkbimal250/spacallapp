import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../api';
import { useAuth } from '../../shared/hooks/useAuth';
import VerificationGate from '../components/VerificationGate';

const AREA_MANAGER_ROLE = 'area_manager';

const Login = () => {
    const [isVerified, setIsVerified] = useState(false);
    const [loginMode, setLoginMode] = useState('phone');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [phoneNumber, setPhoneNumber] = useState('');
    const [otp, setOtp] = useState('');
    const [otpSent, setOtpSent] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const { login } = useAuth();

    const getErrorMessage = (err, fallback) => {
        const data = err.response?.data;
        if (err.response?.status >= 500) {
            return 'Unable to sign in right now. Please try again.';
        }
        if (!data) return fallback;
        if (typeof data.error === 'string') return data.error;
        if (typeof data.detail === 'string') return data.detail;
        const firstFieldError = Object.values(data).flat().find(Boolean);
        return firstFieldError || fallback;
    };

    const requestOtp = async (event) => {
        event.preventDefault();
        const trimmedPhone = phoneNumber.trim();
        if (!trimmedPhone) return;

        setLoading(true);
        setError('');
        try {
            await authAPI.phoneOTP(trimmedPhone);
            setOtpSent(true);
        } catch (err) {
            setError(getErrorMessage(err, 'Unable to send OTP for this phone number.'));
        } finally {
            setLoading(false);
        }
    };

    const handlePasswordLogin = async (event) => {
        event.preventDefault();
        const trimmedEmail = email.trim();
        if (!trimmedEmail || !password) return;

        setLoading(true);
        setError('');
        try {
            const response = await authAPI.login({
                email: trimmedEmail,
                password,
                client: 'web',
            });
            const { access, refresh, user } = response.data;

            if (user?.role !== AREA_MANAGER_ROLE) {
                setError('Access denied: this dashboard is only for area managers.');
                return;
            }

            login({ access, refresh, user });
            navigate('/', { replace: true });
        } catch (err) {
            setError(getErrorMessage(err, 'Invalid email or password.'));
        } finally {
            setLoading(false);
        }
    };

    const verifyOtp = async (event) => {
        event.preventDefault();
        const trimmedPhone = phoneNumber.trim();
        const trimmedOtp = otp.trim();
        if (!trimmedPhone || !trimmedOtp) return;

        setLoading(true);
        setError('');
        try {
            const response = await authAPI.verifyPhoneOTP({
                phone_number: trimmedPhone,
                otp: trimmedOtp,
                client: 'web',
            });
            const { access, refresh, user } = response.data;

            if (user?.role !== AREA_MANAGER_ROLE) {
                setError('Access denied: this dashboard is only for area managers.');
                return;
            }

            login({ access, refresh, user });
            navigate('/', { replace: true });
        } catch (err) {
            setError(getErrorMessage(err, 'Invalid or expired OTP.'));
        } finally {
            setLoading(false);
        }
    };

    if (!isVerified) {
        return <VerificationGate onSuccess={() => setIsVerified(true)} />;
    }

    return (
        <div className="flex min-h-screen items-center justify-center bg-background px-4 animate-in fade-in duration-300">
            <div className="flex w-full max-w-md flex-col items-center">
            <div className="w-full rounded-2xl border border-border bg-card p-6 shadow-lg">
                <div className="mb-6">
                </div>
                <div className="mb-6 grid grid-cols-2 rounded-xl bg-background p-1">
                    <button
                        type="button"
                        onClick={() => {
                            setLoginMode('phone');
                            setError('');
                        }}
                        className={`rounded-lg px-3 py-2 text-sm font-medium transition ${loginMode === 'phone'
                            ? 'bg-primary text-white shadow-soft'
                            : 'text-textSecondary hover:text-textPrimary'
                            }`}
                    >
                        Phone OTP
                    </button>
                    <button
                        type="button"
                        onClick={() => {
                            setLoginMode('password');
                            setError('');
                        }}
                        className={`rounded-lg px-3 py-2 text-sm font-medium transition ${loginMode === 'password'
                            ? 'bg-primary text-white shadow-soft'
                            : 'text-textSecondary hover:text-textPrimary'
                            }`}
                    >
                        Email Password
                    </button>
                </div>

                {error && (
                    <div className="mb-4 rounded-lg border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
                        {error}
                    </div>
                )}

                {loginMode === 'password' ? (
                    <form onSubmit={handlePasswordLogin} className="space-y-4">
                        <label className="block">
                            <span className="mb-1 block text-xs font-semibold uppercase text-textSecondary">Email</span>
                            <input
                                type="email"
                                value={email}
                                onChange={(event) => setEmail(event.target.value)}
                                placeholder="Enter email"
                                className="w-full rounded-lg border border-border bg-background px-4 py-2.5 text-textPrimary outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/30"
                            />
                        </label>
                        <label className="block">
                            <span className="mb-1 block text-xs font-semibold uppercase text-textSecondary">Password</span>
                            <input
                                type="password"
                                value={password}
                                onChange={(event) => setPassword(event.target.value)}
                                placeholder="Enter password"
                                className="w-full rounded-lg border border-border bg-background px-4 py-2.5 text-textPrimary outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/30"
                            />
                        </label>
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full rounded-lg bg-primary px-4 py-2.5 font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                            {loading ? 'Signing in...' : 'Sign in'}
                        </button>
                    </form>
                ) : !otpSent ? (
                    <form onSubmit={requestOtp} className="space-y-4">
                        <label className="block">
                            <span className="mb-1 block text-xs font-semibold uppercase text-textSecondary">Phone Number</span>
                            <input
                                type="tel"
                                value={phoneNumber}
                                onChange={(event) => setPhoneNumber(event.target.value)}
                                placeholder="Enter phone number"
                                className="w-full rounded-lg border border-border bg-background px-4 py-2.5 text-textPrimary outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/30"
                            />
                        </label>
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full rounded-lg bg-primary px-4 py-2.5 font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                            {loading ? 'Sending OTP...' : 'Send OTP'}
                        </button>
                    </form>
                ) : (
                    <form onSubmit={verifyOtp} className="space-y-4">
                        <p className="rounded-lg bg-primarySoft px-3 py-2 text-sm text-textSecondary">
                            OTP sent to <span className="font-semibold text-textPrimary">{phoneNumber}</span>
                        </p>
                        <label className="block">
                            <span className="mb-1 block text-xs font-semibold uppercase text-textSecondary">OTP</span>
                            <input
                                type="text"
                                inputMode="numeric"
                                maxLength="6"
                                value={otp}
                                onChange={(event) => setOtp(event.target.value)}
                                placeholder="------"
                                className="w-full rounded-lg border border-border bg-background px-3 py-3 text-center text-xl tracking-widest text-textPrimary outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/30"
                            />
                        </label>
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full rounded-lg bg-primary px-4 py-2.5 font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                            {loading ? 'Verifying...' : 'Verify OTP'}
                        </button>
                        <button
                            type="button"
                            onClick={() => {
                                setOtpSent(false);
                                setOtp('');
                                setError('');
                            }}
                            className="w-full rounded-lg border border-border px-4 py-2 text-sm font-semibold text-textSecondary transition hover:border-primary hover:text-primary"
                        >
                            Change phone number
                        </button>
                    </form>
                )}
            </div>
            <p className="mt-6 text-xs text-textMuted">Secure Access System</p>
            </div>
        </div>
    );
};

export default Login;
