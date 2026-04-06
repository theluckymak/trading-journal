import { useRouter } from 'next/router';
import Link from 'next/link';
import { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  TrendingUp,
  BarChart3,
  Settings,
  LogOut,
  Calendar,
  MessageSquare,
  Shield,
  ChevronLeft,
  ChevronRight,
  Plus,
  Menu,
  X,
  Brain,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import AddTradeModal from './AddTradeModal';
import ThemeToggle from './ThemeToggle';

export default function Sidebar() {
  const router = useRouter();
  const { logout, user } = useAuth();
  
  const [showTradeModal, setShowTradeModal] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  const [isCollapsed, setIsCollapsed] = useState(() => {
    if (typeof window === 'undefined') return false;
    const saved = localStorage.getItem('sidebarCollapsed');
    if (saved !== null) return saved === 'true';
    return window.innerWidth < 1024;
  });
  
  const [isManuallySet, setIsManuallySet] = useState(() => {
    if (typeof window === 'undefined') return false;
    return localStorage.getItem('sidebarManuallySet') === 'true';
  });

  useEffect(() => {
    const handleResize = () => {
      if (!isManuallySet) {
        const shouldCollapse = window.innerWidth < 1024;
        setIsCollapsed(shouldCollapse);
        localStorage.setItem('sidebarCollapsed', String(shouldCollapse));
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isManuallySet]);
  
  const toggleSidebar = () => {
    const newState = !isCollapsed;
    setIsCollapsed(newState);
    setIsManuallySet(true);
    localStorage.setItem('sidebarCollapsed', String(newState));
    localStorage.setItem('sidebarManuallySet', 'true');
  };

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  const menuItems = [
    { href: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { href: '/trades', icon: TrendingUp, label: 'Trades' },
    { href: '/analytics', icon: BarChart3, label: 'Analytics' },
    { href: '/calendar', icon: Calendar, label: 'Calendar' },
    { href: '/prediction', icon: Brain, label: 'Prediction' },
    { href: '/contact', icon: MessageSquare, label: 'Contact' },
    { href: '/settings', icon: Settings, label: 'Settings' },
  ];

  const adminItems = [
    { href: '/admin', icon: Shield, label: 'Admin Panel' },
  ];

  const isActive = (href: string) => router.pathname === href;

  const iconStyle = "w-[42px] h-[42px] min-w-[42px] min-h-[42px] rounded-full flex items-center justify-center transition-all duration-200";

  return (
    <>
      {/* Mobile Top Bar */}
      <div className="md:hidden" style={{ background: 'var(--bg-section)' }}>
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-3">
            <div className={`${iconStyle}`} style={{ background: 'var(--brand-light)' }}>
              <TrendingUp className="w-5 h-5" style={{ color: 'var(--brand)' }} />
            </div>
            <span className="text-base font-semibold" style={{ color: 'var(--text)' }}>MakTrades</span>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <button
              onClick={() => setShowTradeModal(true)}
              className={iconStyle}
              style={{ background: 'var(--brand-light)', color: 'var(--brand)' }}
              aria-label="Add Trade"
            >
              <Plus className="w-5 h-5" />
            </button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className={iconStyle}
              style={{ background: 'var(--brand-light)', color: 'var(--text-muted)' }}
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
        
        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="p-3" style={{ background: 'var(--bg-section)' }}>
            <nav className="space-y-1">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center gap-3 px-2 py-2 rounded-2xl transition-all"
                  >
                    <div className={iconStyle} style={{
                      background: active ? 'var(--brand-light)' : 'transparent',
                      color: active ? 'var(--brand)' : 'var(--text-muted)',
                    }}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="text-sm font-medium" style={{ color: active ? 'var(--text)' : 'var(--text-muted)' }}>
                      {item.label}
                    </span>
                  </Link>
                );
              })}
              
              {user?.role === 'ADMIN' && adminItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center gap-3 px-2 py-2 rounded-2xl transition-all"
                  >
                    <div className={iconStyle} style={{
                      background: active ? 'rgba(245,166,35,0.1)' : 'transparent',
                      color: active ? 'var(--warning)' : 'var(--text-muted)',
                    }}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="text-sm font-medium" style={{ color: active ? 'var(--text)' : 'var(--text-muted)' }}>
                      {item.label}
                    </span>
                  </Link>
                );
              })}
              
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-2 py-2 rounded-2xl transition-all"
                style={{ color: 'var(--text-muted)' }}
              >
                <div className={iconStyle}>
                  <LogOut className="w-5 h-5" />
                </div>
                <span className="text-sm font-medium">Logout</span>
              </button>
            </nav>
          </div>
        )}
      </div>

      {/* Desktop Sidebar */}
      <div
        className={`hidden md:flex h-screen ${isCollapsed ? 'w-[76px]' : 'w-64'} flex-col transition-all duration-300 ease-in-out`}
        style={{ background: 'var(--bg-section)', borderRight: '1px solid var(--border)' }}
      >
        {/* Logo */}
        <div className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={iconStyle} style={{ background: 'var(--brand-light)' }}>
                <TrendingUp className="w-5 h-5" style={{ color: 'var(--brand)' }} />
              </div>
              {!isCollapsed && <span className="text-lg font-semibold" style={{ color: 'var(--text)' }}>MakTrades</span>}
            </div>
            {!isCollapsed && (
              <button
                onClick={toggleSidebar}
                className="w-8 h-8 min-w-[32px] min-h-[32px] rounded-full flex items-center justify-center transition-colors"
                style={{ color: 'var(--text-muted)' }}
                title="Collapse sidebar"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {isCollapsed && (
          <button
            onClick={toggleSidebar}
            className="mx-auto mt-1 w-8 h-8 min-w-[32px] min-h-[32px] rounded-full flex items-center justify-center transition-colors"
            style={{ color: 'var(--text-muted)' }}
            title="Expand sidebar"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        )}

        {/* Navigation */}
        <nav className="flex-1 px-3 overflow-y-auto mt-4">
          <div className="mb-5 flex justify-center">
            <button
              onClick={() => setShowTradeModal(true)}
              className={iconStyle}
              style={{ background: 'var(--brand)', color: '#FFFFFF' }}
              title="Add Trade"
            >
              <Plus className="w-5 h-5" />
            </button>
          </div>

          <ul className="space-y-1">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);
              
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-2 py-2 rounded-2xl transition-all duration-200 group`}
                    title={isCollapsed ? item.label : ''}
                  >
                    <div className={iconStyle} style={{
                      background: active ? 'var(--brand-light)' : 'transparent',
                      color: active ? 'var(--brand)' : 'var(--text-muted)',
                    }}>
                      <Icon className="w-5 h-5" />
                    </div>
                    {!isCollapsed && (
                      <span className="text-sm font-medium" style={{ color: active ? 'var(--text)' : 'var(--text-muted)' }}>
                        {item.label}
                      </span>
                    )}
                  </Link>
                </li>
              );
            })}
            
            {user?.role === 'ADMIN' && (
              <>
                {!isCollapsed && (
                  <li className="pt-4 mt-4" style={{ borderTop: '1px solid var(--border)' }}>
                    <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                      Admin
                    </p>
                  </li>
                )}
                {adminItems.map((item) => {
                  const Icon = item.icon;
                  const active = isActive(item.href);
                  
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-2 py-2 rounded-2xl transition-all duration-200 group`}
                        title={isCollapsed ? item.label : ''}
                      >
                        <div className={iconStyle} style={{
                          background: active ? 'rgba(245,166,35,0.1)' : 'transparent',
                          color: active ? 'var(--warning)' : 'var(--text-muted)',
                        }}>
                          <Icon className="w-5 h-5" />
                        </div>
                        {!isCollapsed && (
                          <span className="text-sm font-medium" style={{ color: active ? 'var(--text)' : 'var(--text-muted)' }}>
                            {item.label}
                          </span>
                        )}
                      </Link>
                    </li>
                  );
                })}
              </>
            )}
          </ul>
        </nav>

        {/* Bottom */}
        <div className="p-3 space-y-2">
          {/* Theme Toggle */}
          <div className={`flex ${isCollapsed ? 'justify-center' : 'px-2'}`}>
            <ThemeToggle />
          </div>
          
          <button
            onClick={handleLogout}
            className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-2 py-2 rounded-2xl transition-all duration-200 group`}
            title={isCollapsed ? 'Logout' : ''}
            style={{ color: 'var(--text-muted)' }}
          >
            <div className={`${iconStyle} group-hover:text-[var(--error)]`}>
              <LogOut className="w-5 h-5" />
            </div>
            {!isCollapsed && <span className="text-sm font-medium">Logout</span>}
          </button>
        </div>

        {/* User Info */}
        {!isCollapsed && user && (
          <div className="p-4" style={{ borderTop: '1px solid var(--border)' }}>
            <div className="flex items-center gap-3 px-2 py-3 rounded-2xl" style={{ background: 'var(--brand-light)' }}>
              <div className={iconStyle} style={{ background: 'var(--brand)', color: '#FFFFFF', fontSize: '14px', fontWeight: 700 }}>
                {user.email?.charAt(0)?.toUpperCase() || 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate" style={{ color: 'var(--text)' }}>{user.email}</p>
                <p className="text-[11px]" style={{ color: 'var(--text-muted)' }}>{user.role || 'Trader'}</p>
              </div>
            </div>
          </div>
        )}

        <AddTradeModal
          isOpen={showTradeModal}
          onClose={() => setShowTradeModal(false)}
          onSuccess={() => router.push('/dashboard')}
        />
      </div>
    </>
  );
}
