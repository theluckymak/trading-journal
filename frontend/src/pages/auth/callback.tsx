import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { apiClient } from '@/lib/api';

export default function AuthCallback() {
  const router = useRouter();
  const [debugInfo, setDebugInfo] = useState<string>('');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Check for hash fragment (Google OAuth)
        const hash = window.location.hash.substring(1);
        const params = new URLSearchParams(hash);
        const accessToken = params.get('access_token');
        const state = params.get('state');

        // Check for query params (GitHub OAuth)
        const query = new URLSearchParams(window.location.search);
        const code = query.get('code');
        const queryState = query.get('state');

        const provider = state || queryState;

        const debugMsg = `URL: ${window.location.href}\nHash: ${hash}\nToken: ${accessToken ? 'Present' : 'Missing'}\nProvider: ${provider}`;
        setDebugInfo(debugMsg);
        console.log('=== OAuth Callback Debug ===');
        console.log('Full URL:', window.location.href);
        console.log('Hash:', hash);
        console.log('Access Token:', accessToken ? 'Present' : 'Missing');
        console.log('State:', state);
        console.log('Provider:', provider);

        if (!provider || !['google', 'github'].includes(provider)) {
          console.error('Invalid provider detected');
          setDebugInfo(prev => prev + '\n\nERROR: Invalid provider');
          throw new Error('Invalid OAuth provider');
        }

        let token = accessToken;

        // For GitHub, exchange code for token
        if (code && provider === 'github') {
          // GitHub requires server-side exchange
          const response = await fetch('https://github.com/login/oauth/access_token', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            body: JSON.stringify({
              client_id: process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID,
              client_secret: '', // Should be stored on backend
              code: code,
            }),
          });
          const data = await response.json();
          token = data.access_token;
        }

        if (!token) {
          setDebugInfo(prev => prev + '\n\nERROR: No token received');
          throw new Error('No access token received');
        }

        setDebugInfo(prev => prev + '\n\nSending to backend...');
        console.log('Sending token to backend:', provider);

        // Send token to backend for verification and user creation
        const response = await fetch(`https://dependable-solace-production-75f7.up.railway.app/api/auth/oauth/${provider}/token`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ access_token: token }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'OAuth authentication failed');
        }

        const data = await response.json();
        const { access_token, refresh_token } = data;
        
        // Save tokens
        localStorage.setItem('accessToken', access_token);
        localStorage.setItem('refreshToken', refresh_token);
        
        // Fetch actual user data from backend
        const userResponse = await fetch('https://dependable-solace-production-75f7.up.railway.app/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${access_token}`,
          },
        });
        
        if (userResponse.ok) {
          const userData = await userResponse.json();
          sessionStorage.setItem('user', JSON.stringify(userData));
        }

        setDebugInfo(prev => prev + '\n\nSuccess! Redirecting...');
        console.log('Login successful, redirecting to dashboard');

        // Redirect to dashboard
        router.push('/dashboard');
      } catch (error: any) {
        console.error('OAuth callback error:', error);
        console.error('Error details:', error.response?.data || error.message);
        const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
        setDebugInfo(prev => prev + `\n\nERROR: ${errorMsg}`);
        
        // Don't redirect immediately on error so user can see the debug info
        setTimeout(() => {
          router.push('/login?error=oauth_failed');
        }, 5000);
      }
    };

    handleCallback();
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <div className="max-w-2xl w-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Completing sign in...</p>
        </div>
        
        {debugInfo && (
          <div className="mt-8 p-4 bg-gray-100 rounded-lg">
            <h3 className="font-semibold mb-2">Debug Info:</h3>
            <pre className="text-xs whitespace-pre-wrap text-left">{debugInfo}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

