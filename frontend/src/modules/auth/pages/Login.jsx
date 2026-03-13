import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { loginStart, loginSuccess, loginFailure } from '../../../store/slices/authSlice';
import { authAPI } from '../api';
import { setToken, setUser } from '../../../shared/services/tokenService';
import { Mail, Lock } from 'lucide-react';

const Login = () => {

    const [loginMode, setLoginMode] = useState('password');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [otp, setOtp] = useState('');
    const [otpSent, setOtpSent] = useState(false);
    const [requestLoading, setRequestLoading] = useState(false);

    const dispatch = useDispatch();
    const navigate = useNavigate();
    const { loading, error } = useSelector((state) => state.auth);

    const handlePasswordLogin = async (e) => {
        e.preventDefault();
        dispatch(loginStart());
        try {
            const response = await authAPI.login({ email, password });
            handleAuthSuccess(response);
        } catch (err) {
            dispatch(loginFailure(err.response?.data?.error || 'Invalid credentials'));
        }
    };

    const handleRequestOTP = async (e) => {
        e.preventDefault();
        setRequestLoading(true);
        dispatch(loginFailure(null));
        try {
            await authAPI.requestOTP(email);
            setOtpSent(true);
        } catch (err) {
            dispatch(loginFailure(err.response?.data?.error || 'Failed to send OTP'));
        } finally {
            setRequestLoading(false);
        }
    };

    const handleVerifyOTP = async (e) => {
        e.preventDefault();
        dispatch(loginStart());
        try {
            const response = await authAPI.verifyOTP({ email, otp });
            handleAuthSuccess(response);
        } catch (err) {
            dispatch(loginFailure(err.response?.data?.error || 'Invalid OTP'));
        }
    };

    const handleAuthSuccess = (response) => {

        const { access, refresh, user: userData } = response.data;

        if (userData && userData.role === 'branch_manager') {
            dispatch(loginFailure('Access Denied: Branch Managers must use the Android App.'));
            return;
        }

        setToken(access);

        if (refresh) {
            localStorage.setItem('refresh', refresh);
        }

        const userToStore = userData || { email, role: 'super_admin' };

        setUser(userToStore);
        dispatch(loginSuccess(userToStore));
        navigate('/');

    };

    return (

        <div className="w-full max-w-md">

            <div className="bg-card border border-border rounded-xl shadow-lg p-8">

                {/* Header */}

                <div className="text-center mb-8">

                    <h1 className="text-xl font-semibold text-text-primary">
                        Admin Login
                    </h1>

                    <p className="text-sm text-text-secondary mt-1">
                        Access the management dashboard
                    </p>

                </div>


                {/* Tabs */}

                <div className="flex bg-background rounded-lg p-1 mb-6">

                    <button
                        onClick={() => {
                            setLoginMode('password');
                            setOtpSent(false);
                            dispatch(loginFailure(null));
                        }}
                        className={`flex-1 py-2 text-sm font-medium rounded-md transition ${loginMode === 'password'
                            ? 'bg-cardHover text-text-primary'
                            : 'text-text-muted'
                            }`}
                    >
                        Password
                    </button>

                    <button
                        onClick={() => {
                            setLoginMode('otp');
                            dispatch(loginFailure(null));
                        }}
                        className={`flex-1 py-2 text-sm font-medium rounded-md transition ${loginMode === 'otp'
                            ? 'bg-cardHover text-text-primary'
                            : 'text-text-muted'
                            }`}
                    >
                        OTP Login
                    </button>

                </div>


                {/* Error */}

                {error && (
                    <div className="mb-4 p-3 text-sm bg-danger/10 border border-danger/30 text-danger rounded-lg">
                        {error}
                    </div>
                )}


                {/* Password Login */}

                {loginMode === 'password' ? (

                    <form onSubmit={handlePasswordLogin} className="space-y-4">

                        <div className="relative">

                            <Mail className="absolute left-3 top-3.5 h-4 w-4 text-text-muted" />

                            <input
                                type="email"
                                required
                                placeholder="Email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full pl-10 pr-4 py-2.5 bg-background border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:ring-2 focus:ring-primary outline-none"
                            />

                        </div>

                        <div className="relative">

                            <Lock className="absolute left-3 top-3.5 h-4 w-4 text-text-muted" />

                            <input
                                type="password"
                                required
                                placeholder="Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full pl-10 pr-4 py-2.5 bg-background border border-border rounded-lg text-text-primary placeholder:text-text-muted focus:ring-2 focus:ring-primary outline-none"
                            />

                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-2.5 bg-primary hover:bg-primary-hover text-white font-semibold rounded-lg transition"
                        >
                            {loading ? 'Signing in...' : 'Sign In'}
                        </button>

                    </form>

                ) : (

                    <div className="space-y-4">

                        {!otpSent ? (

                            <form onSubmit={handleRequestOTP} className="space-y-4">

                                <div className="relative">

                                    <Mail className="absolute left-3 top-3.5 h-4 w-4 text-text-muted" />

                                    <input
                                        type="email"
                                        required
                                        placeholder="Email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="w-full pl-10 pr-4 py-2.5 bg-background border border-border rounded-lg text-text-primary focus:ring-2 focus:ring-primary outline-none"
                                    />

                                </div>

                                <button
                                    type="submit"
                                    disabled={requestLoading}
                                    className="w-full py-2.5 bg-primary hover:bg-primary-hover text-white font-semibold rounded-lg"
                                >
                                    {requestLoading ? 'Sending...' : 'Send OTP'}
                                </button>

                            </form>

                        ) : (

                            <form onSubmit={handleVerifyOTP} className="space-y-4">

                                <div className="text-sm bg-info/10 border border-info/30 text-info p-3 rounded-lg">
                                    OTP sent to <span className="font-medium">{email}</span>
                                </div>

                                <input
                                    type="text"
                                    maxLength="6"
                                    value={otp}
                                    onChange={(e) => setOtp(e.target.value)}
                                    placeholder="Enter OTP"
                                    className="w-full py-2.5 text-center text-lg tracking-widest bg-background border border-border rounded-lg text-text-primary focus:ring-2 focus:ring-primary outline-none"
                                />

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full py-2.5 bg-primary hover:bg-primary-hover text-white font-semibold rounded-lg"
                                >
                                    {loading ? 'Verifying...' : 'Verify OTP'}
                                </button>

                                <button
                                    type="button"
                                    onClick={() => setOtpSent(false)}
                                    className="text-xs text-text-muted hover:text-primary"
                                >
                                    Change Email
                                </button>

                            </form>

                        )}

                    </div>

                )}

            </div>

        </div>

    );

};

export default Login;