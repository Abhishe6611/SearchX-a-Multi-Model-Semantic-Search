import { Search, X } from 'lucide-react';
import { useState } from 'react';

export default function SearchBar({ onSearch, searchMode }) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(query);
  };

  const handleClear = () => {
    setQuery('');
    onSearch('');
  };

  return (
    <div className="mb-6">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative group">
          {/* subtle background glow when focused or hovered */}
          <div className="absolute inset-0 bg-gradient-to-r from-aurora-cyan to-aurora-violet rounded-full blur opacity-0 group-hover:opacity-20 focus-within:opacity-40 transition-opacity duration-500"></div>
          
          <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-hover:text-aurora-cyan transition-colors duration-300 z-10" />
          
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search images and documents using natural language..."
            className="
              relative w-full pl-12 pr-12 py-3 
              bg-slate-900/60 backdrop-blur-xl border border-white/10 
              rounded-full text-sm text-white placeholder-slate-500 font-medium
              shadow-[inset_0_2px_10px_rgba(0,0,0,0.5)]
              focus:outline-none focus:ring-2 focus:ring-aurora-cyan/50 focus:border-aurora-cyan
              transition-all duration-300 z-0
            "
          />

          {query && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute right-5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white bg-slate-800/80 p-1 rounded-full backdrop-blur-sm transition-colors z-10"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {searchMode && (
          <div className="mt-4 flex items-center justify-center gap-3 text-sm animate-in fade-in slide-in-from-top-2 duration-300">
            <div className="px-4 py-1.5 bg-aurora-cyan/10 border border-aurora-cyan/30 rounded-full text-aurora-cyan shadow-[0_0_15px_rgba(6,182,212,0.2)] font-medium">
              Active Search Session
            </div>
            <button
              type="button"
              onClick={handleClear}
              className="px-4 py-1.5 text-slate-300 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 rounded-full transition-colors"
            >
              Clear
            </button>
          </div>
        )}
      </form>

      <div className="mt-3 text-xs text-slate-500">
        <p>💡 Try: "sunset landscape", "financial report", "person smiling", "contract document"</p>
      </div>
    </div>
  );
}
