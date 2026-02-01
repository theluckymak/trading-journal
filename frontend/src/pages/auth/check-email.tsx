import { useRouter } from 'next/router';
import { useState } from 'react';
import Head from 'next/head';

const API_URL = 'https://dependable-solace-production-75f7.up.railway.app';

export default function CheckEmail() {
  const router = useRouter();
  const { email } = router.query;
  const [resending, setResending] = useState(false);
  const [resent, setResent] = useState(false);
  const [error, setError] = useState('');

  const handleResend = async () => {
    if (!email) return;
    
    setResending(true);
    setError('');
    
    try {
      const response = await fetch(`${API_URL}/api/auth/resend-verification?email=${encodeURIComponent(email as string)}`, {
        method: 'POST',
      });
      
      if (response.ok) {
        setResent(true);
        setTimeout(() => setResent(false), 5000);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to resend email');
      }
    } catch (err) {
      setError('Failed to resend email. Please try again.');
    } finally {
      setResending(false);
    }
  };

  return (
    <>
      <Head>
        <title>Check Your Email - Trading Journal</title>
      </Head>
      
      <div className="min-h-screen flex items-center justify-center bg-gray-900 px-4">
        <div className="max-w-md w-full bg-gray-800 rounded-lg shadow-xl p-8 text-center">
          {/* Email Icon */}
          <div className="mx-auto w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mb-6">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          
          <h1 className="text-2xl font-bold text-white mb-4">Check Your Email</h1>
          
          <p className="text-gray-300 mb-2">
            We've sent a verification link to:
          </p>
          
          {email && (
            <p className="text-blue-400 font-medium mb-6">
              {email}
            </p>
          )}
          
          <div className="bg-gray-700/50 rounded-lg p-4 mb-6 text-left">
            <p className="text-gray-300 text-sm mb-3">
              <strong className="text-white">Important:</strong> The email might be in your spam folder.
            </p>
            <ul className="text-gray-400 text-sm space-y-2">
              <li className="flex items-start">
                <span className="text-blue-400 mr-2">•</span>
                Check your spam/junk folder
              </li>
              <li className="flex items-start">
                <span className="text-blue-400 mr-2">•</span>
                Mark the email as "Not Spam"
              </li>
              <li className="flex items-start">
                <span className="text-blue-400 mr-2">•</span>
                Add no-reply@maktrades.app to contacts
              </li>
            </ul>
          </div>
          
          {error && (
            <div className="bg-red-500/20 border border-red-500 rounded-lg p-3 mb-4">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}
          
          {resent && (
            <div className="bg-green-500/20 border border-green-500 rounded-lg p-3 mb-4">
              <p className="text-green-400 text-sm">Verification email resent!</p>
            </div>
          )}
          
          <div className="space-y-3">
            <button
              onClick={handleResend}
              disabled={resending || !email}
              className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
            >
              {resending ? 'Sending...' : 'Resend Verification Email'}
            </button>
            
            <button
              onClick={() => router.push('/auth/login')}
              className="w-full py-3 px-4 bg-gray-700 hover:bg-gray-600 text-white font-medium rounded-lg transition-colors"
            >
              Back to Login
            </button>
          </div>
          
          <p className="text-gray-500 text-xs mt-6">
            Already verified? You can log in now.
          </p>
        </div>
      </div>
    </>
  );
}
