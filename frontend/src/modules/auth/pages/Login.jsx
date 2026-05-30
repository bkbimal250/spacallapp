import React from 'react';
import VerificationGate from '../components/VerificationGate';
import LoginPage from './LoginPage';

const Login = () => {
    return (
        <VerificationGate>
            <LoginPage />
        </VerificationGate>
    );
};

export default Login;
