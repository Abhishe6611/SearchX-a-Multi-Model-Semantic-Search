import { Image, FileText, Loader2, Trash2, Download, Eye, Search } from 'lucide-react';
import { getThumbnailUrl, getDownloadUrl } from '../services/api';

// Status badge component
function StatusBadge({ status }) {
  const configs = {
    success: {
      color: 'bg-green-500',
      label: 'Processed',
      animate: false
    },
    pending: {
      color: 'bg-orange-500',
      label: 'Processing',
      animate: true
    },
    failed: {
      color: 'bg-red-500',
      label: 'Failed',
      animate: false
    }
  };

  const config = configs[status] || configs.pending;

  return (
    <div className="absolute top-2 right-2 flex items-center gap-1.5 px-2 py-1 bg-slate-900/90 backdrop-blur-sm rounded-full">
      <div className={`w-2 h-2 rounded-full ${config.color} ${config.animate ? 'animate-pulse-slow' : ''}`}></div>
      <span className="text-xs text-white font-medium">{config.label}</span>
    </div>
  );
}

// File card component
function FileCard({ file, onFileClick, onDelete }) {
  const isImage = file.file_type?.startsWith('image/');
  const thumbnailUrl = getThumbnailUrl(file.thumbnail_path);
  
  const handleDelete = (e) => {
    e.stopPropagation();
    onDelete(file.id);
  };

  const handleDownload = (e) => {
    e.stopPropagation();
    window.open(getDownloadUrl(file.id), '_blank');
  };

  return (
    <div
      onClick={() => onFileClick(file)}
      className="
        group relative glass-panel rounded-2xl overflow-hidden
        hover:-translate-y-2 hover:shadow-[0_15px_30px_rgba(0,0,0,0.5)]
        transition-all duration-300 cursor-pointer
      "
    >
      {/* Thumbnail */}
      <div className="aspect-square bg-slate-900/50 flex items-center justify-center overflow-hidden">
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt={file.original_filename}
            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
            loading="lazy"
          />
        ) : (
          <div className="flex flex-col items-center gap-2 text-slate-600 group-hover:scale-110 transition-transform duration-500">
            {isImage ? (
              <Image className="w-16 h-16 drop-shadow-md" />
            ) : (
              <FileText className="w-16 h-16 drop-shadow-md" />
            )}
          </div>
        )}
      </div>

      {/* Status Badge */}
      <StatusBadge status={file.processing_status} />

      {/* File Info */}
      <div className="p-4 border-t border-white/5 bg-slate-900/40">
        <h3 className="text-sm font-semibold text-white truncate mb-1">
          {file.original_filename}
        </h3>
        
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span className="truncate font-medium">
            {(file.file_size / 1024).toFixed(0)} KB
          </span>
          
          {file.relevance_score !== undefined && (
            <span className="px-2.5 py-0.5 bg-aurora-cyan/20 text-aurora-cyan rounded-full font-bold shadow-[0_0_10px_rgba(6,182,212,0.2)]">
              {(file.relevance_score * 100).toFixed(0)}% match
            </span>
          )}
        </div>

        {/* Date */}
        <div className="mt-2 text-[10px] uppercase font-bold text-slate-500 tracking-wider">
          {new Date(file.upload_date).toLocaleDateString()}
        </div>
      </div>

      {/* Action Buttons (appear on hover) */}
      <div className="
        absolute inset-0 bg-slate-900/60 backdrop-blur-md
        opacity-0 group-hover:opacity-100 transition-opacity duration-300
        flex items-center justify-center gap-3
      ">
        <button
          onClick={(e) => { e.stopPropagation(); onFileClick(file); }}
          className="p-3 bg-aurora-cyan hover:bg-cyan-400 text-slate-900 hover:scale-110 rounded-xl transition-all shadow-[0_0_20px_rgba(6,182,212,0.4)]"
          title="View"
        >
          <Eye className="w-5 h-5" />
        </button>
        
        <button
          onClick={handleDownload}
          className="p-3 bg-white/10 hover:bg-white/20 border border-white/10 text-white hover:scale-110 rounded-xl transition-all"
          title="Download"
        >
          <Download className="w-5 h-5" />
        </button>
        
        <button
          onClick={handleDelete}
          className="p-3 bg-rose-500/20 hover:bg-rose-500 border border-rose-500/50 hover:border-transparent text-rose-300 hover:text-white hover:scale-110 rounded-xl transition-all shadow-[0_0_15px_rgba(225,29,72,0)] hover:shadow-[0_0_15px_rgba(225,29,72,0.5)]"
          title="Delete"
        >
          <Trash2 className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}

// Main file grid component
export default function FileGrid({ files, loading, searchMode, searchQuery, onFileClick, onDelete }) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="w-12 h-12 text-primary-500 animate-spin" />
        <p className="mt-4 text-slate-400">Loading files...</p>
      </div>
    );
  }

  if (files.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="glass-panel p-10 rounded-3xl text-center max-w-md shadow-2xl relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-aurora-cyan/5 to-aurora-violet/5"></div>
          <div className="relative z-10">
            {searchMode ? (
              <>
                <Search className="w-16 h-16 text-slate-500 mx-auto mb-5" />
                <h3 className="text-2xl font-display font-semibold text-white mb-2">
                  No results found
                </h3>
                <p className="text-slate-400 font-medium">
                  Try a different search query or adjust your terms
                </p>
                {searchQuery && (
                  <p className="mt-3 text-sm text-slate-500 bg-black/20 px-3 py-1.5 rounded-full inline-block border border-white/5">
                    Searched for: <span className="text-aurora-cyan">"{searchQuery}"</span>
                  </p>
                )}
              </>
            ) : (
              <>
                <Image className="w-16 h-16 text-slate-500 mx-auto mb-5 drop-shadow-md" />
                <h3 className="text-2xl font-display font-semibold text-white mb-2 tracking-tight">
                  Vault is Empty
                </h3>
                <p className="text-slate-400 font-medium">
                  Upload some images or documents to get started
                </p>
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">
          {searchMode ? `Search Results (${files.length})` : `All Files (${files.length})`}
        </h2>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {files.map((file) => (
          <FileCard
            key={file.id}
            file={file}
            onFileClick={onFileClick}
            onDelete={onDelete}
          />
        ))}
      </div>
    </div>
  );
}
