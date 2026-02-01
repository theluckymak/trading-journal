import { ReactNode } from 'react';
import Sidebar from './Sidebar';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <>
      {/* Mobile: Top bar layout */}
      <div className="md:hidden flex flex-col h-screen bg-[#0a0f1a]">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
      
      {/* Desktop: Sidebar layout */}
      <div className="hidden md:flex h-screen bg-[#0a0f1a]">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </>
  );
}
