/**
 * Home/landing page.
 */
import { useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, loading } = useAuth();

  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Trading Journal & Analytics
          </h1>
          <p className="text-xl text-gray-600 mb-12 max-w-2xl mx-auto">
            Professional trading journal with MT5 integration. Track your trades,
            analyze performance, and improve your trading strategy.
          </p>
          
          <div className="flex gap-4 justify-center">
            <Link href="/register" className="btn-primary text-lg px-8 py-3">
              Get Started
            </Link>
            <Link href="/login" className="btn-secondary text-lg px-8 py-3">
              Sign In
            </Link>
          </div>
        </div>

        <div className="mt-20 grid md:grid-cols-3 gap-8">
          <div className="card text-center">
            <div className="text-4xl mb-4">📊</div>
            <h3 className="text-xl font-semibold mb-2">Analytics</h3>
            <p className="text-gray-600">
              Win rate, profit factor, expectancy, and detailed performance metrics
            </p>
          </div>

          <div className="card text-center">
            <div className="text-4xl mb-4">🔗</div>
            <h3 className="text-xl font-semibold mb-2">MT5 Integration</h3>
            <p className="text-gray-600">
              Automatic trade import from MetaTrader 5 with secure credentials
            </p>
          </div>

          <div className="card text-center">
            <div className="text-4xl mb-4">📝</div>
            <h3 className="text-xl font-semibold mb-2">Trade Journal</h3>
            <p className="text-gray-600">
              Detailed notes, tags, screenshots, and analysis for every trade
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
