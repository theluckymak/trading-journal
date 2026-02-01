import { ReactNode } from 'react';
import Sidebar from './Sidebar';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <>
      {/* Mobile: Top bar layout */}
      <div className="md:hidden flex flex-col h-screen bg-[#0a0f1a] relative overflow-hidden">
        {/* Gradient orbs */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-500/[0.07] rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-purple-500/[0.05] rounded-full blur-[100px] pointer-events-none" />
        <Sidebar />
        <main className="flex-1 overflow-y-auto relative z-10">
          {children}
        </main>
      </div>
      
      {/* Desktop: Sidebar layout */}
      <div className="hidden md:flex h-screen bg-[#0a0f1a] relative overflow-hidden">
        {/* Gradient orbs */}
        <div className="absolute top-[-10%] right-[10%] w-[600px] h-[600px] bg-blue-500/[0.07] rounded-full blur-[150px] pointer-events-none" />
        <div className="absolute bottom-[-10%] left-[20%] w-[500px] h-[500px] bg-purple-500/[0.05] rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute top-[40%] right-[30%] w-[300px] h-[300px] bg-cyan-500/[0.04] rounded-full blur-[100px] pointer-events-none" />
        <Sidebar />
        <main className="flex-1 overflow-y-auto relative z-10">
          {children}
        </main>
      </div>
    </>
  );
}
