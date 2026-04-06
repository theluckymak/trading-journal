/**
 * Home/landing page.
 */
import { useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import ThemeToggle from '@/components/ThemeToggle';

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
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--bg)' }}>
        <div className="text-xl" style={{ color: 'var(--text-muted)' }}>Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg)' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="absolute top-4 right-4">
          <ThemeToggle />
        </div>
        <div className="text-center">
          <h1 className="text-5xl font-bold mb-6" style={{ color: 'var(--text)' }}>
            Trading Journal & Analytics
          </h1>
          <p className="text-xl mb-12 max-w-2xl mx-auto" style={{ color: 'var(--text-muted)' }}>
            Professional trading journal with MT5 integration. Track your trades,
            analyze performance, and improve your trading strategy.
          </p>
          
          <div className="flex gap-4 justify-center">
            <Link href="/register" className="btn btn-brand text-lg px-8 py-3">
              Get Started
            </Link>
            <Link href="/login" className="btn btn-secondary text-lg px-8 py-3">
              Sign In
            </Link>
          </div>
        </div>

        <div className="mt-20 grid md:grid-cols-3 gap-8">
          <div className="card text-center">
            <div className="text-4xl mb-4"></div>
            <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text)' }}>Analytics</h3>
            <p style={{ color: 'var(--text-muted)' }}>
              Win rate, profit factor, expectancy, and detailed performance metrics
            </p>
          </div>

          <div className="card text-center">
            <div className="text-4xl mb-4"></div>
            <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text)' }}>MT5 Integration</h3>
            <p style={{ color: 'var(--text-muted)' }}>
              Automatic trade import from MetaTrader 5 with secure credentials
            </p>
          </div>

          <div className="card text-center">
            <div className="text-4xl mb-4"></div>
            <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text)' }}>Trade Journal</h3>
            <p style={{ color: 'var(--text-muted)' }}>
              Detailed notes, tags, screenshots, and analysis for every trade
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
