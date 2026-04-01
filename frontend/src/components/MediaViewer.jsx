import { X, Download, Trash2, ZoomIn, ZoomOut, Maximize2, ChevronLeft, ChevronRight } from 'lucide-react';
import { useState, useEffect } from 'react';
import { getFileUrl, getThumbnailUrl, getDownloadUrl } from '../services/api';

export default function MediaViewer({ file, onClose, onDelete }) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const isImage = file.file_type?.startsWith('image/');
  const isPDF = file.file_type === 'application/pdf';
  const isText = file.file_type === 'text/plain';
  const fileUrl = getFileUrl(file.file_path);

  // Reset zoom and pan when file changes
  useEffect(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, [file.id]);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.25, 0.5));
  const handleResetZoom = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleMouseDown = (e) => {
    if (zoom > 1) {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleDelete = () => {
    onDelete(file.id);
    onClose();
  };

  const handleDownload = () => {
    window.open(getDownloadUrl(file.id), '_blank');
  };

  return (
    <div
      className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-2xl flex items-center justify-center animate-in fade-in duration-300"
      onClick={onClose}
    >
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 glass-panel border-b border-white/5 p-4 z-10 shadow-xl">
        <div className="container mx-auto flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <h2 className="text-xl font-display font-semibold text-white tracking-tight truncate">
              {file.original_filename}
            </h2>
            <div className="flex items-center gap-3 mt-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-400">
              <span className="bg-white/10 px-2 py-1 rounded-md text-white">{(file.file_size / 1024).toFixed(0)} KB</span>
              <span>{new Date(file.upload_date).toLocaleDateString()}</span>
              {file.relevance_score && (
                <>
                  <span className="text-aurora-cyan shadow-[0_0_10px_rgba(6,182,212,0.5)]">
                    {(file.relevance_score * 100).toFixed(0)}% match
                  </span>
                </>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {isImage && (
              <>
                <button
                  onClick={(e) => { e.stopPropagation(); handleZoomOut(); }}
                  className="p-2.5 bg-white/5 hover:bg-white/10 rounded-xl transition-colors border border-transparent hover:border-white/10"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-5 h-5 text-white" />
                </button>
                
                <button
                  onClick={(e) => { e.stopPropagation(); handleResetZoom(); }}
                  className="p-2.5 bg-white/5 hover:bg-white/10 rounded-xl transition-colors text-xs text-white font-medium min-w-[3.5rem] border border-transparent hover:border-white/10"
                  title="Reset Zoom"
                >
                  {Math.round(zoom * 100)}%
                </button>
                
                <button
                  onClick={(e) => { e.stopPropagation(); handleZoomIn(); }}
                  className="p-2.5 bg-white/5 hover:bg-white/10 rounded-xl transition-colors border border-transparent hover:border-white/10"
                  title="Zoom In"
                >
                  <ZoomIn className="w-5 h-5 text-white" />
                </button>
                
                <div className="w-px h-6 bg-white/10 mx-2"></div>
              </>
            )}
            
            <button
              onClick={(e) => { e.stopPropagation(); handleDownload(); }}
              className="p-2.5 bg-aurora-cyan/20 hover:bg-aurora-cyan text-aurora-cyan hover:text-slate-900 border border-aurora-cyan/30 rounded-xl transition-all shadow-[0_0_15px_rgba(6,182,212,0)] hover:shadow-[0_0_15px_rgba(6,182,212,0.5)]"
              title="Download"
            >
              <Download className="w-5 h-5" />
            </button>
            
            <button
              onClick={(e) => { e.stopPropagation(); handleDelete(); }}
              className="p-2.5 bg-rose-500/20 hover:bg-rose-500 border border-rose-500/30 text-rose-300 hover:text-white rounded-xl transition-all shadow-[0_0_15px_rgba(225,29,72,0)] hover:shadow-[0_0_15px_rgba(225,29,72,0.5)]"
              title="Delete"
            >
              <Trash2 className="w-5 h-5" />
            </button>
            
            <div className="w-px h-6 bg-white/10 mx-2"></div>
            
            <button
              onClick={onClose}
              className="p-2.5 bg-white/10 hover:bg-white/20 rounded-xl transition-all hover:rotate-90"
              title="Close"
            >
              <X className="w-5 h-5 text-white" />
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div
        className="relative w-full h-full flex items-center justify-center p-20"
        onClick={(e) => e.stopPropagation()}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{ cursor: zoom > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default' }}
      >
        {isImage && (
          <img
            src={fileUrl}
            alt={file.original_filename}
            className="max-w-full max-h-full object-contain select-none"
            style={{
              transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
              transition: isDragging ? 'none' : 'transform 0.2s ease-out'
            }}
            draggable={false}
          />
        )}

        {isPDF && (
          <div className="w-full h-full bg-white rounded-lg overflow-hidden">
            <iframe
              src={fileUrl}
              className="w-full h-full"
              title={file.original_filename}
            />
          </div>
        )}

        {isText && (
          <div className="w-full max-w-4xl h-full bg-slate-800 rounded-lg overflow-auto p-8">
            <pre className="text-slate-200 font-mono text-sm whitespace-pre-wrap">
              {file.extracted_text || 'Loading...'}
            </pre>
          </div>
        )}

        {!isImage && !isPDF && !isText && (
          <div className="text-center">
            <p className="text-white text-lg mb-4">Preview not available</p>
            <button
              onClick={handleDownload}
              className="px-6 py-3 bg-primary-500 hover:bg-primary-600 rounded-lg text-white font-medium transition-colors"
            >
              Download File
            </button>
          </div>
        )}
      </div>

      {/* Extracted Text Panel (for images with OCR) */}
      {isImage && file.extracted_text && file.extracted_text.trim() && (
        <div className="absolute bottom-6 left-0 right-0 p-4 z-10 pointer-events-none">
          <div className="container mx-auto max-w-4xl">
            <details className="glass-panel backdrop-blur-3xl rounded-2xl p-6 pointer-events-auto border border-aurora-cyan/20 shadow-[0_0_30px_rgba(0,0,0,0.5)]">
              <summary className="text-white font-display font-semibold cursor-pointer mb-3 outline-none select-none flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-aurora-cyan animate-pulse"></span>
                Extracted Text (AI OCR)
              </summary>
              <div className="text-sm text-slate-300 max-h-48 overflow-y-auto pr-2 custom-scrollbar font-sans leading-relaxed">
                {file.extracted_text}
              </div>
            </details>
          </div>
        </div>
      )}
    </div>
  );
}
