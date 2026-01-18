import { useRouter } from 'next/router';
import Link from 'next/link';
import { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  TrendingUp,
  BookOpen,
  BarChart3,
  Settings,
  LogOut,
  Sun,
  Moon,
  Calendar,
  MessageSquare,
  Shield,
  ChevronLeft,
  ChevronRight,
  Plus,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import AddTradeModal from './AddTradeModal';
import AddJournalModal from './AddJournalModal';

export default function Sidebar() {
  const router = useRouter();
  const { logout, user } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  
  // Modal states
  const [showTradeModal, setShowTradeModal] = useState(false);
  const [showJournalModal, setShowJournalModal] = useState(false);
  
  // Initialize state from localStorage immediately
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
    { href: '/journal', icon: BookOpen, label: 'Journal' },
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
    <div className={`h-screen ${isCollapsed ? 'w-20' : 'w-64'} bg-white dark:bg-gray-800 border-r dark:border-gray-700 flex flex-col transition-all duration-300 ease-in-out`}>
      {/* Logo */}
      <div className="p-6 border-b dark:border-gray-700">
        <div className="flex items-center justify-between mb-2">
          {!isCollapsed && <h1 className="text-xl font-bold text-gray-900 dark:text-white transition-opacity duration-200">Trading Journal</h1>}
          {isCollapsed && <span className="text-xl font-bold text-gray-900 dark:text-white mx-auto">TJ</span>}
          <button
            onClick={toggleSidebar}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors duration-200"
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
          </button>
        </div>
        {!isCollapsed && <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 transition-opacity duration-200">Track your progress</p>}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 overflow-y-auto">
        {/* Quick Add Buttons */}
        <div className="mb-4 space-y-2">
          <button
            onClick={() => setShowTradeModal(true)}
            className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-4 py-3 bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-all duration-200`}
            title={isCollapsed ? 'Add Trade' : ''}
          >
            <Plus className="h-5 w-5 flex-shrink-0" />
            {!isCollapsed && <span className="font-medium transition-opacity duration-200">Add Trade</span>}
          </button>
          <button
            onClick={() => setShowJournalModal(true)}
            className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-4 py-3 bg-green-600 text-white hover:bg-green-700 rounded-lg transition-all duration-200`}
            title={isCollapsed ? 'Add Journal' : ''}
          >
            <Plus className="h-5 w-5 flex-shrink-0" />
            {!isCollapsed && <span className="font-medium transition-opacity duration-200">Add Journal</span>}
          </button>
        </div>

        <ul className="space-y-2">{menuItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-4 py-3 rounded-lg transition-all duration-200 ${
                    active
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                  title={isCollapsed ? item.label : ''}
                >
                  <Icon className="h-5 w-5 flex-shrink-0" />
                  {!isCollapsed && <span className="font-medium transition-opacity duration-200">{item.label}</span>}
                </Link>
              </li>
            );
          })}
          
          {/* Admin Items */}
          {user?.role === 'admin' && (
            <>
              {!isCollapsed && (
                <li className="pt-2 mt-2 border-t dark:border-gray-700">
                  <p className="px-4 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
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
                      className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-4 py-3 rounded-lg transition-all duration-200 ${
                        active
                          ? 'bg-orange-600 text-white'
                          : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                      title={isCollapsed ? item.label : ''}
                    >
                      <Icon className="h-5 w-5 flex-shrink-0" />
                      {!isCollapsed && <span className="font-medium transition-opacity duration-200">{item.label}</span>}
                    </Link>
                  </li>
                );
              })}
            </>
          )}
        </ul>
      </nav>

      {/* Bottom Actions */}
      <div className="p-4 border-t dark:border-gray-700 space-y-2">
        <button
          onClick={toggleTheme}
          className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-4 py-3 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-all duration-200`}
          title={isCollapsed ? (isDark ? 'Light Mode' : 'Dark Mode') : ''}
        >
          {isDark ? <Sun className="h-5 w-5 flex-shrink-0" /> : <Moon className="h-5 w-5 flex-shrink-0" />}
          {!isCollapsed && <span className="font-medium transition-opacity duration-200">{isDark ? 'Light Mode' : 'Dark Mode'}</span>}
        </button>
        <button
          onClick={handleLogout}
          className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'gap-3'} px-4 py-3 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all duration-200`}
          title={isCollapsed ? 'Logout' : ''}
        >
          <LogOut className="h-5 w-5 flex-shrink-0" />
          {!isCollapsed && <span className="font-medium transition-opacity duration-200">Logout</span>}
        </button>
      </div>

      {/* Modals */}
      <AddTradeModal
        isOpen={showTradeModal}
        onClose={() => setShowTradeModal(false)}
        onSuccess={() => router.push('/dashboard')}
      />
      <AddJournalModal
        isOpen={showJournalModal}
        onClose={() => setShowJournalModal(false)}
        onSuccess={() => router.push('/journal')}
      />
    </div>
  );
}
