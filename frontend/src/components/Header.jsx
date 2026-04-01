import { Search as SearchIcon, Settings } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Header() {
  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-white/5 shadow-[0_4px_30px_rgba(0,0,0,0.1)]">
      <div className="container mx-auto px-4 py-2">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-4 group">
            <div className="relative">
              <div className="absolute inset-0 bg-aurora-cyan rounded-xl blur-md opacity-50 group-hover:opacity-100 transition-opacity duration-300"></div>
              <div className="relative bg-gradient-to-br from-aurora-indigo to-aurora-cyan p-2.5 rounded-xl shadow-lg border border-white/10 group-hover:scale-105 transition-transform duration-300">
                <SearchIcon className="w-5 h-5 text-white" />
              </div>
            </div>
            <div>
              <h1 className="text-xl font-display font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-400 tracking-tight">
                SearchX
              </h1>
              <p className="text-[10px] text-aurora-cyan font-medium tracking-wide uppercase mt-0.5">
                Semantic Media Search
              </p>
            </div>
          </Link>

          <div className="flex items-center gap-6 text-sm text-slate-300">
            <Link
              to="/admin"
              className="flex items-center gap-2 px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-aurora-cyan/50 text-slate-200 text-xs rounded-lg transition-all duration-300 hover:shadow-[0_0_15px_rgba(6,182,212,0.3)]"
            >
              <Settings className="w-3.5 h-3.5" />
              <span className="hidden md:inline font-medium">Admin Dashboard</span>
            </Link>
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/20">
              <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse shadow-[0_0_8px_rgba(74,222,128,0.8)]"></div>
              <span className="text-green-400 font-medium text-xs">System Online</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
