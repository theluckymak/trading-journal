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
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import AddTradeModal from './AddTradeModal';

export default function Sidebar() {
  const router = useRouter();
  const { logout, user } = useAuth();
  
  // Modal states
  const [showTradeModal, setShowTradeModal] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  // Initialize state from localStorage immediately (desktop only)
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

  // Always use dark mode
  useEffect(() => {
    document.documentElement.classList.add('dark');
  }, []);
  
  // Handle responsive behavior on window resize
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
    { href: '/contact', icon: MessageSquare, label: 'Contact' },
    { href: '/settings', icon: Settings, label: 'Settings' },
  ];

  // Admin-only menu items
  const adminItems = [
    { href: '/admin', icon: Shield, label: 'Admin Panel' },
  ];

  const isActive = (href: string) => router.pathname === href;

  // Icon wrapper style - perfectly round
  const iconStyle = "w-[42px] h-[42px] min-w-[42px] min-h-[42px] rounded-full flex items-center justify-center";

  return (
    <>
      {/* Mobile Top Bar */}
      <div className="md:hidden bg-[#0a0f1a]">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-3">
            <div className={`${iconStyle} bg-gradient-to-br from-cyan-400/80 to-blue-500/80`}>
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <span className="text-base font-semibold text-white">MakTrades</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowTradeModal(true)}
              className={`${iconStyle} bg-white/10 text-cyan-400/80 hover:bg-white/15 transition-colors`}
              aria-label="Add Trade"
            >
              <Plus className="w-5 h-5" />
            </button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className={`${iconStyle} bg-white/10 text-slate-400 hover:bg-white/15 transition-colors`}
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
        
        {/* Mobile Menu Dropdown */}
        {mobileMenuOpen && (
          <div className="p-3 bg-[#0a0f1a]">
            <nav className="space-y-1">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-2 py-2 rounded-2xl transition-all ${
                      active
                        ? 'bg-white/5 text-white'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <div className={`${iconStyle} ${
                      active ? 'bg-gradient-to-br from-cyan-400/80 to-blue-500/80 text-white' : 'bg-white/10'
                    }`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="text-sm font-medium">{item.label}</span>
                  </Link>
                );
              })}
              
              {user?.role === 'admin' && adminItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-2 py-2 rounded-2xl transition-all ${
                      active
                        ? 'bg-white/5 text-white'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <div className={`${iconStyle} ${
                      active ? 'bg-gradient-to-br from-orange-400/80 to-red-500/80 text-white' : 'bg-white/10'
                    }`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="text-sm font-medium">{item.label}</span>
                  </Link>
                );
              })}
              
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-2 py-2 text-slate-400 hover:text-red-400/80 rounded-2xl transition-all"
              >
                <div className={`${iconStyle} bg-white/10`}>
                  <LogOut className="w-5 h-5" />
                </div>
                <span className="text-sm font-medium">Logout</span>
              </button>
            </nav>
          </div>
        )}
      </div>

      {/* Desktop Sidebar - No borders */}
      <div className={`hidden md:flex h-screen ${isCollapsed ? 'w-[76px]' : 'w-64'} bg-[#0a0f1a] flex-col transition-all duration-300 ease-in-out`}>
        {/* Logo */}
        <div className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`${iconStyle} bg-gradient-to-br from-cyan-400/80 to-blue-500/80`}>
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              {!isCollapsed && <span className="text-lg font-semibold text-white">MakTrades</span>}
            </div>
            {!isCollapsed && (
              <button
                onClick={toggleSidebar}
                className="w-8 h-8 min-w-[32px] min-h-[32px] rounded-full bg-white/10 hover:bg-white/15 text-slate-500 transition-colors flex items-center justify-center"
                title="Collapse sidebar"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Expand button when collapsed */}
        {isCollapsed && (
          <button
            onClick={toggleSidebar}
            className="mx-auto mt-1 w-8 h-8 min-w-[32px] min-h-[32px] rounded-full bg-white/10 hover:bg-white/15 text-slate-500 transition-colors flex items-center justify-center"
            title="Expand sidebar"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        )}

        {/* Navigation */}
        <nav className="flex-1 px-3 overflow-y-auto mt-4">
          {/* Quick Add Button */}
          <div className="mb-5 px-1">
            <button
              onClick={() => setShowTradeModal(true)}
              className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-2 py-2 bg-white/5 text-cyan-400/80 hover:bg-white/10 rounded-2xl transition-all duration-200`}
              title={isCollapsed ? 'Add Trade' : ''}
            >
              <div className={`${iconStyle} bg-gradient-to-br from-cyan-400/80 to-blue-500/80`}>
                <Plus className="w-5 h-5 text-white" />
              </div>
              {!isCollapsed && <span className="text-sm font-medium">Add Trade</span>}
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
                    className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-2 py-2 rounded-2xl transition-all duration-200 group ${
                      active
                        ? 'bg-white/5 text-white'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                    title={isCollapsed ? item.label : ''}
                  >
                    <div className={`${iconStyle} transition-all ${
                      active 
                        ? 'bg-gradient-to-br from-cyan-400/80 to-blue-500/80 text-white' 
                        : 'bg-white/10 group-hover:bg-white/15'
                    }`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    {!isCollapsed && <span className="text-sm font-medium">{item.label}</span>}
                  </Link>
                </li>
              );
            })}
            
            {/* Admin Items */}
            {user?.role === 'admin' && (
              <>
                {!isCollapsed && (
                  <li className="pt-4 mt-4">
                    <p className="px-3 mb-2 text-[10px] font-semibold text-slate-600 uppercase tracking-wider">
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
                        className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-2 py-2 rounded-2xl transition-all duration-200 group ${
                          active
                            ? 'bg-white/5 text-white'
                            : 'text-slate-400 hover:text-slate-200'
                        }`}
                        title={isCollapsed ? item.label : ''}
                      >
                        <div className={`${iconStyle} transition-all ${
                          active 
                            ? 'bg-gradient-to-br from-orange-400/80 to-red-500/80 text-white' 
                            : 'bg-white/10 group-hover:bg-white/15'
                        }`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        {!isCollapsed && <span className="text-sm font-medium">{item.label}</span>}
                      </Link>
                    </li>
                  );
                })}
              </>
            )}
          </ul>
        </nav>

        {/* Bottom Actions */}
        <div className="p-3">
          <button
            onClick={handleLogout}
            className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-2 py-2 text-slate-400 hover:text-red-400/80 rounded-2xl transition-all duration-200 group`}
            title={isCollapsed ? 'Logout' : ''}
          >
            <div className={`${iconStyle} bg-white/10 group-hover:bg-red-500/15 transition-all`}>
              <LogOut className="w-5 h-5" />
            </div>
            {!isCollapsed && <span className="text-sm font-medium">Logout</span>}
          </button>
        </div>

        {/* User Info */}
        {!isCollapsed && user && (
          <div className="p-4">
            <div className="flex items-center gap-3 px-2 py-3 rounded-2xl bg-white/5">
              <div className={`${iconStyle} bg-gradient-to-br from-slate-600 to-slate-700 text-sm font-bold text-white uppercase`}>
                {user.email?.charAt(0) || 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{user.email}</p>
                <p className="text-[11px] text-slate-500">{user.role || 'Trader'}</p>
              </div>
            </div>
          </div>
        )}

        {/* Modals */}
        <AddTradeModal
          isOpen={showTradeModal}
          onClose={() => setShowTradeModal(false)}
          onSuccess={() => router.push('/dashboard')}
        />
      </div>
    </>
  );
}
