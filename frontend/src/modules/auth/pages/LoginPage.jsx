import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { loginFailure, loginStart, loginSuccess } from '../../../store/slices/authSlice';
import { setToken, setUser } from '../../../shared/services/tokenService';
import { authAPI } from '../api';
import { Phone } from 'lucide-react';

const MAIN_CRM_ROLES = ['admin', 'super_admin'];

const LoginPage = () => {
    const [loginMode, setLoginMode] = useState('phoneOtp');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [otp, setOtp] = useState('');
    const [otpSent, setOtpSent] = useState(false);
    const [phoneNumber, setPhoneNumber] = useState('');
    const [phoneOtp, setPhoneOtp] = useState('');
    const [phoneOtpSent, setPhoneOtpSent] = useState(false);
    const [requestLoading, setRequestLoading] = useState(false);

    const dispatch = useDispatch();
    const navigate = useNavigate();
    const { loading, error } = useSelector((state) => state.auth);

    const getErrorMessage = (err, fallback) => {
        const data = err.response?.data;
        if (!data) return fallback;
        if (typeof data.error === 'string') return data.error;
        if (typeof data.detail === 'string') return data.detail;
        const firstFieldError = Object.values(data).flat().find(Boolean);
        return firstFieldError || fallback;
    };

    const switchLoginMode = (mode) => {
        setLoginMode(mode);
        setOtpSent(false);
        setPhoneOtpSent(false);
        setOtp('');
        setPhoneOtp('');
        dispatch(loginFailure(null));
    };

    const handlePasswordLogin = async (e) => {
        e.preventDefault();
        const trimmedEmail = email.trim();
        if (!trimmedEmail || !password) return;

        dispatch(loginStart());
        try {
            const response = await authAPI.login({ email: trimmedEmail, password, client: 'web' });
            handleAuthSuccess(response);
        } catch (err) {
            dispatch(loginFailure(getErrorMessage(err, 'Invalid credentials')));
        }
    };

    const handleRequestOTP = async (e) => {
        e.preventDefault();
        const trimmedEmail = email.trim();
        if (!trimmedEmail) return;

        setRequestLoading(true);
        dispatch(loginFailure(null));
        try {
            await authAPI.requestOTP(trimmedEmail);
            setOtpSent(true);
        } catch (err) {
            console.error('OTP Request Error:', err.response?.data);
            dispatch(loginFailure(getErrorMessage(err, 'Failed to send OTP. Please check if the user exists.')));
        } finally {
            setRequestLoading(false);
        }
    };

    const handleVerifyOTP = async (e) => {
        e.preventDefault();
        const trimmedEmail = email.trim();
        if (!trimmedEmail || !otp) return;

        dispatch(loginStart());
        try {
            const response = await authAPI.verifyOTP({ email: trimmedEmail, otp: otp.trim(), client: 'web' });
            handleAuthSuccess(response);
        } catch (err) {
            dispatch(loginFailure(getErrorMessage(err, 'Invalid or expired OTP')));
        }
    };

    const handleRequestPhoneOTP = async (e) => {
        e.preventDefault();
        const trimmedPhone = phoneNumber.trim();
        if (!trimmedPhone) return;

        setRequestLoading(true);
        dispatch(loginFailure(null));
        try {
            await authAPI.phoneOTP(trimmedPhone);
            setPhoneOtpSent(true);
        } catch (err) {
            dispatch(loginFailure(getErrorMessage(err, 'Failed to send OTP. Please check the phone number.')));
        } finally {
            setRequestLoading(false);
        }
    };

    const handleVerifyPhoneOTP = async (e) => {
        e.preventDefault();
        const trimmedPhone = phoneNumber.trim();
        if (!trimmedPhone || !phoneOtp) return;

        dispatch(loginStart());
        try {
            const response = await authAPI.verifyPhoneOTP({
                phone_number: trimmedPhone,
                otp: phoneOtp.trim(),
                client: 'web',
            });
            handleAuthSuccess(response);
        } catch (err) {
            dispatch(loginFailure(getErrorMessage(err, 'Invalid or expired OTP')));
        }
    };

    const handleAuthSuccess = (response) => {
        const { access, refresh, user: userData } = response.data;

        if (userData?.role && !MAIN_CRM_ROLES.includes(userData.role)) {
            dispatch(loginFailure('Access denied: this CRM is only for admin and super admin users.'));
            return;
        }

        setToken(access);
        if (refresh) {
            localStorage.setItem('refresh', refresh);
        }

        const userToStore = userData || { email: email.trim(), phone_number: phoneNumber.trim(), role: 'super_admin' };
        setUser(userToStore);
        dispatch(loginSuccess(userToStore));
        navigate('/');
    };

    return (
        <div className="w-full max-w-md px-4 flex flex-col items-center animate-auth-fade">
            <div className="w-full bg-card border border-border rounded-2xl p-6 shadow-lg">
                <div className="grid grid-cols-3 bg-background p-1 rounded-xl mb-6">
                    <button
                        type="button"
                        onClick={() => switchLoginMode('phoneOtp')}
                        className={`py-2 text-sm font-medium rounded-lg transition flex items-center justify-center gap-1.5 ${loginMode === 'phoneOtp'
                                ? 'bg-primary text-white'
                                : 'text-text-secondary'
                            }`}
                    >
                        <Phone size={14} />
                        Phone OTP
                    </button>

                    <button
                        type="button"
                        onClick={() => switchLoginMode('password')}
                        className={`py-2 text-sm font-medium rounded-lg transition ${loginMode === 'password'
                                ? 'bg-primary text-white'
                                : 'text-text-secondary'
                            }`}
                    >
                        Password
                    </button>

                    <button
                        type="button"
                        onClick={() => switchLoginMode('otp')}
                        className={`py-2 text-sm font-medium rounded-lg transition ${loginMode === 'otp'
                                ? 'bg-primary text-white'
                                : 'text-text-secondary'
                            }`}
                    >
                        OTP
                    </button>
                </div>

                {error && (
                    <div className="mb-4 px-3 py-2 text-sm bg-danger/10 border border-danger/30 text-danger rounded-lg">
                        {error}
                    </div>
                )}

                {loginMode === 'phoneOtp' && (
                    <div className="space-y-4">
                        {!phoneOtpSent ? (
                            <form onSubmit={handleRequestPhoneOTP} className="space-y-4">
                                <input
                                    type="tel"
                                    placeholder="Enter Phone Number"
                                    value={phoneNumber}
                                    onChange={(e) => setPhoneNumber(e.target.value)}
                                    className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:ring-2 focus:ring-primary/30 outline-none"
                                />

                                <button
                                    type="submit"
                                    disabled={requestLoading}
                                    className="w-full py-2.5 bg-primary hover:bg-primary-hover text-white rounded-lg font-semibold transition"
                                >
                                    {requestLoading ? 'Sending...' : 'Send OTP'}
                                </button>
                            </form>
                        ) : (
                            <form onSubmit={handleVerifyPhoneOTP} className="space-y-4">
                                <p className="text-sm text-text-secondary text-center">
                                    OTP sent to <span className="text-text-primary font-semibold">{phoneNumber}</span>
                                </p>

                                <input
                                    type="text"
                                    inputMode="numeric"
                                    maxLength="6"
                                    value={phoneOtp}
                                    onChange={(e) => setPhoneOtp(e.target.value)}
                                    placeholder="------"
                                    className="w-full text-center text-xl tracking-widest py-3 bg-background border border-border rounded-lg text-text-primary focus:ring-2 focus:ring-primary/30 outline-none"
                                />

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full py-2.5 bg-primary hover:bg-primary-hover text-white rounded-lg font-semibold transition"
                                >
                                    {loading ? 'Verifying...' : 'Verify'}
                                </button>

                                <button
                                    type="button"
                                    onClick={() => setPhoneOtpSent(false)}
                                    className="text-sm text-text-muted w-full hover:text-primary transition"
                                >
                                    Change Phone Number
                                </button>
                            </form>
                        )}
                    </div>
                )}

                {loginMode === 'password' && (
                    <form onSubmit={handlePasswordLogin} className="space-y-4">
                        <input
                            type="email"
                            placeholder="Email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:ring-2 focus:ring-primary/30 outline-none"
                        />

                        <input
                            type="password"
                            placeholder="Password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:ring-2 focus:ring-primary/30 outline-none"
                        />

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-2.5 bg-primary hover:bg-primary-hover text-white rounded-lg font-semibold flex justify-center items-center gap-2 transition"
                        >
                            {loading ? 'Loading...' : 'Login'}
                        </button>
                    </form>
                )}

                {loginMode === 'otp' && (
                    <div className="space-y-4">
                        {!otpSent ? (
                            <form onSubmit={handleRequestOTP} className="space-y-4">
                                <input
                                    type="email"
                                    placeholder="Enter Email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full px-4 py-2.5 bg-background border border-border rounded-lg text-text-primary focus:ring-2 focus:ring-primary/30 outline-none"
                                />

                                <button
                                    type="submit"
                                    disabled={requestLoading}
                                    className="w-full py-2.5 bg-primary hover:bg-primary-hover text-white rounded-lg font-semibold transition"
                                >
                                    {requestLoading ? 'Sending...' : 'Send OTP'}
                                </button>
                            </form>
                        ) : (
                            <form onSubmit={handleVerifyOTP} className="space-y-4">
                                <p className="text-sm text-text-secondary text-center">
                                    OTP sent to <span className="text-text-primary font-semibold">{email}</span>
                                </p>

                                <input
                                    type="text"
                                    inputMode="numeric"
                                    maxLength="6"
                                    value={otp}
                                    onChange={(e) => setOtp(e.target.value)}
                                    placeholder="------"
                                    className="w-full text-center text-xl tracking-widest py-3 bg-background border border-border rounded-lg text-text-primary focus:ring-2 focus:ring-primary/30 outline-none"
                                />

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full py-2.5 bg-primary hover:bg-primary-hover text-white rounded-lg font-semibold transition"
                                >
                                    {loading ? 'Verifying...' : 'Verify'}
                                </button>

                                <button
                                    type="button"
                                    onClick={() => setOtpSent(false)}
                                    className="text-sm text-text-muted w-full hover:text-primary transition"
                                >
                                    Change Email
                                </button>
                            </form>
                        )}
                    </div>
                )}
            </div>

            <p className="mt-6 text-xs text-text-muted">
                Secure Access System
            </p>
        </div>
    );
};

export default LoginPage;
