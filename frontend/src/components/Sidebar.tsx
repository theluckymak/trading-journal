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

  return (
    <>
      {/* Mobile Top Bar */}
      <div className="md:hidden bg-[#0f1419] border-b border-slate-800/50">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-amber-500/80 to-amber-600/80 flex items-center justify-center">
              <TrendingUp className="h-4 w-4 text-slate-900" />
            </div>
            <span className="text-base font-semibold text-slate-200">MakTrades</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowTradeModal(true)}
              className="p-2 bg-amber-500/20 text-amber-400/90 rounded-xl hover:bg-amber-500/30 transition-colors border border-amber-500/20"
              aria-label="Add Trade"
            >
              <Plus size={18} />
            </button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-slate-400 hover:bg-slate-800/50 rounded-xl transition-colors"
            >
              {mobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
            </button>
          </div>
        </div>
        
        {/* Mobile Menu Dropdown */}
        {mobileMenuOpen && (
          <div className="border-t border-slate-800/50 p-3 bg-[#0f1419]">
            <nav className="space-y-1">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
                      active
                        ? 'bg-slate-800/60 text-slate-100'
                        : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-300'
                    }`}
                  >
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      active ? 'bg-amber-500/20 text-amber-400/90' : 'bg-slate-800/60'
                    }`}>
                      <Icon size={16} />
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
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
                      active
                        ? 'bg-slate-800/60 text-slate-100'
                        : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-300'
                    }`}
                  >
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      active ? 'bg-orange-500/20 text-orange-400/80' : 'bg-slate-800/60'
                    }`}>
                      <Icon size={16} />
                    </div>
                    <span className="text-sm font-medium">{item.label}</span>
                  </Link>
                );
              })}
              
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-3 py-2.5 text-slate-400 hover:bg-red-500/10 hover:text-red-400/80 rounded-xl transition-all"
              >
                <div className="w-8 h-8 rounded-lg bg-slate-800/60 flex items-center justify-center">
                  <LogOut size={16} />
                </div>
                <span className="text-sm font-medium">Logout</span>
              </button>
            </nav>
          </div>
        )}
      </div>

      {/* Desktop Sidebar */}
      <div className={`hidden md:flex h-screen ${isCollapsed ? 'w-[72px]' : 'w-60'} bg-[#0f1419] border-r border-slate-800/50 flex-col transition-all duration-300 ease-in-out`}>
        {/* Logo */}
        <div className="p-4 border-b border-slate-800/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-500/80 to-amber-600/80 flex items-center justify-center shadow-lg shadow-amber-500/10">
                <TrendingUp className="h-5 w-5 text-slate-900" />
              </div>
              {!isCollapsed && <span className="text-base font-semibold text-slate-200">MakTrades</span>}
            </div>
            {!isCollapsed && (
              <button
                onClick={toggleSidebar}
                className="p-1.5 rounded-lg hover:bg-slate-800/50 text-slate-500 transition-colors"
                title="Collapse sidebar"
              >
                <ChevronLeft size={16} />
              </button>
            )}
          </div>
        </div>

        {/* Expand button when collapsed */}
        {isCollapsed && (
          <button
            onClick={toggleSidebar}
            className="mx-auto mt-3 p-1.5 rounded-lg hover:bg-slate-800/50 text-slate-500 transition-colors"
            title="Expand sidebar"
          >
            <ChevronRight size={16} />
          </button>
        )}

        {/* Navigation */}
        <nav className="flex-1 p-3 overflow-y-auto mt-2">
          {/* Quick Add Button */}
          <div className="mb-4">
            <button
              onClick={() => setShowTradeModal(true)}
              className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-3 py-2.5 bg-amber-500/15 border border-amber-500/20 text-amber-400/90 hover:bg-amber-500/25 rounded-xl transition-all duration-200`}
              title={isCollapsed ? 'Add Trade' : ''}
            >
              <div className={`${isCollapsed ? '' : 'w-7 h-7'} rounded-lg ${isCollapsed ? '' : 'bg-amber-500/20'} flex items-center justify-center`}>
                <Plus className="h-4 w-4" />
              </div>
              {!isCollapsed && <span className="text-sm font-medium">Add Trade</span>}
            </button>
          </div>

          {!isCollapsed && (
            <p className="px-3 mb-2 text-[10px] font-semibold text-slate-600 uppercase tracking-wider">Menu</p>
          )}

          <ul className="space-y-1">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);
              
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-3 py-2.5 rounded-xl transition-all duration-200 group ${
                      active
                        ? 'bg-slate-800/60 text-slate-100'
                        : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-300'
                    }`}
                    title={isCollapsed ? item.label : ''}
                  >
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
                      active 
                        ? 'bg-amber-500/20 text-amber-400/90' 
                        : 'bg-slate-800/60 group-hover:bg-slate-700/60'
                    }`}>
                      <Icon className="h-4 w-4" />
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
                  <li className="pt-4 mt-4 border-t border-slate-800/50">
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
                        className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-3 py-2.5 rounded-xl transition-all duration-200 group ${
                          active
                            ? 'bg-slate-800/60 text-slate-100'
                            : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-300'
                        }`}
                        title={isCollapsed ? item.label : ''}
                      >
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
                          active 
                            ? 'bg-orange-500/20 text-orange-400/80' 
                            : 'bg-slate-800/60 group-hover:bg-slate-700/60'
                        }`}>
                          <Icon className="h-4 w-4" />
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
        <div className="p-3 border-t border-slate-800/50 space-y-1">
          <button
            onClick={handleLogout}
            className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-3 py-2.5 text-slate-400 hover:bg-red-500/10 hover:text-red-400/80 rounded-xl transition-all duration-200 group`}
            title={isCollapsed ? 'Logout' : ''}
          >
            <div className="w-8 h-8 rounded-lg bg-slate-800/60 group-hover:bg-red-500/20 flex items-center justify-center transition-colors">
              <LogOut className="h-4 w-4" />
            </div>
            {!isCollapsed && <span className="text-sm font-medium">Logout</span>}
          </button>
        </div>

        {/* User Info */}
        {!isCollapsed && user && (
          <div className="p-3 border-t border-slate-800/50">
            <div className="flex items-center gap-3 px-3 py-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center text-xs font-bold text-slate-300 uppercase">
                {user.email?.charAt(0) || 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-300 truncate">{user.email}</p>
                <p className="text-[10px] text-slate-500 uppercase">{user.role || 'Trader'}</p>
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
