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
        <div className="absolute top-[5%] right-[-10%] w-[300px] h-[300px] bg-blue-500/[0.08] rounded-full blur-[80px] pointer-events-none" />
        <div className="absolute bottom-[20%] left-[-15%] w-[250px] h-[250px] bg-purple-500/[0.07] rounded-full blur-[70px] pointer-events-none" />
        <div className="absolute top-[50%] right-[-5%] w-[200px] h-[200px] bg-cyan-500/[0.06] rounded-full blur-[60px] pointer-events-none" />
        <Sidebar />
        <main className="flex-1 overflow-y-auto relative z-10">
          {children}
        </main>
      </div>
      
      {/* Desktop: Sidebar layout */}
      <div className="hidden md:flex h-screen bg-[#0a0f1a] relative overflow-hidden">
        {/* Left side orbs */}
        <div className="absolute top-[10%] left-[5%] w-[400px] h-[400px] bg-indigo-500/[0.06] rounded-full blur-[120px] pointer-events-none" />
        <div className="absolute bottom-[15%] left-[-5%] w-[350px] h-[350px] bg-violet-500/[0.07] rounded-full blur-[100px] pointer-events-none" />
        
        {/* Right side orbs */}
        <div className="absolute top-[-5%] right-[5%] w-[500px] h-[500px] bg-blue-500/[0.08] rounded-full blur-[130px] pointer-events-none" />
        <div className="absolute top-[40%] right-[-10%] w-[400px] h-[400px] bg-cyan-500/[0.06] rounded-full blur-[110px] pointer-events-none" />
        <div className="absolute bottom-[-10%] right-[15%] w-[450px] h-[450px] bg-teal-500/[0.05] rounded-full blur-[120px] pointer-events-none" />
        
        {/* Center accent */}
        <div className="absolute top-[60%] left-[40%] w-[300px] h-[300px] bg-purple-500/[0.04] rounded-full blur-[100px] pointer-events-none" />
        
        <Sidebar />
        <main className="flex-1 overflow-y-auto relative z-10">
          {children}
        </main>
      </div>
    </>
  );
}
