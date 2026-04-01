import { Upload, FileText, Image, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadFiles } from '../services/api';

export default function UploadZone({ onUploadComplete }) {
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState([]);
  const [showResults, setShowResults] = useState(false);

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;

    setUploading(true);
    setUploadResults([]);
    setShowResults(true);

    try {
      const response = await uploadFiles(acceptedFiles);
      setUploadResults(response.files || []);
      
      if (onUploadComplete) {
        setTimeout(onUploadComplete, 1000);
      }
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadResults([{
        filename: 'Upload',
        success: false,
        error: error.message || 'Upload failed'
      }]);
    } finally {
      setUploading(false);
    }
  }, [onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.webp'],
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt']
    },
    multiple: true
  });

  return (
    <div className="mb-6 relative group">
      {/* Decorative background glow behind the zone */}
      <div className="absolute inset-0 bg-gradient-to-r from-aurora-cyan/10 to-aurora-indigo/10 blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
      
      <div
        {...getRootProps()}
        className={`
          relative rounded-2xl p-8 text-center overflow-hidden
          transition-all duration-300 cursor-pointer glass-panel
          ${isDragActive 
            ? 'border-aurora-cyan bg-aurora-cyan/5 scale-[1.02] shadow-[0_0_30px_rgba(6,182,212,0.3)]' 
            : 'hover:border-white/20 hover:bg-white/5 shadow-lg'
          }
        `}
      >
        {/* Animated Dashed Border (Using an SVG pseudo-element or complex border, here we simplify using tailwind border-dashed with glowing colors) */}
        <div className={`absolute inset-0 border-2 border-dashed rounded-3xl transition-colors duration-300 ${isDragActive ? 'border-aurora-cyan' : 'border-white/10 group-hover:border-white/20'}`}></div>

        <input {...getInputProps()} />
        
        <div className="relative z-10 flex flex-col items-center gap-4">
          <div className={`p-3 rounded-xl transition-all duration-300 ${isDragActive ? 'bg-aurora-cyan shadow-[0_0_20px_rgba(6,182,212,0.5)] scale-110' : 'bg-gradient-to-br from-aurora-indigo to-aurora-cyan shadow-lg group-hover:scale-105'}`}>
            <Upload className="w-6 h-6 text-white" />
          </div>
          
          <div>
            <h3 className="text-lg font-display font-semibold text-white mb-1 tracking-tight">
              {isDragActive ? 'Drop files to awaken...' : 'Synthesize New Media'}
            </h3>
            <p className="text-slate-400 text-sm mb-4 font-medium">
              Drag & drop or click to ingest documents and images
            </p>
            <div className="flex flex-wrap gap-3 justify-center text-xs font-semibold text-aurora-cyan">
              <span className="px-3 py-1 bg-aurora-cyan/10 border border-aurora-cyan/20 rounded-full backdrop-blur-sm">Images</span>
              <span className="px-3 py-1 bg-aurora-indigo/10 border border-aurora-indigo/20 rounded-full backdrop-blur-sm text-indigo-300">PDF</span>
              <span className="px-3 py-1 bg-aurora-violet/10 border border-aurora-violet/20 rounded-full backdrop-blur-sm text-violet-300">DOCX</span>
              <span className="px-3 py-1 bg-white/5 border border-white/10 rounded-full backdrop-blur-sm text-slate-300">TXT</span>
            </div>
          </div>
        </div>

        {uploading && (
          <div className="absolute inset-0 z-20 bg-slate-950/80 backdrop-blur-md flex items-center justify-center">
            <div className="flex flex-col items-center gap-4">
              <Loader2 className="w-12 h-12 text-aurora-cyan animate-spin drop-shadow-[0_0_10px_rgba(6,182,212,0.8)]" />
              <p className="text-white font-medium tracking-wide animate-pulse">Ingesting files...</p>
            </div>
          </div>
        )}
      </div>

      {/* Upload Results */}
      {showResults && uploadResults.length > 0 && !uploading && (
        <div className="mt-4 bg-slate-800/50 rounded-xl p-4 border border-slate-700">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-white">Upload Results</h4>
            <button
              onClick={() => setShowResults(false)}
              className="text-xs text-slate-400 hover:text-white transition-colors"
            >
              Close
            </button>
          </div>
          
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {uploadResults.map((result, idx) => (
              <div
                key={idx}
                className={`
                  flex items-center gap-3 px-3 py-2 rounded-lg text-sm
                  ${result.success ? 'bg-green-500/10' : 'bg-red-500/10'}
                `}
              >
                {result.success ? (
                  <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                )}
                
                <span className="flex-1 text-slate-300 truncate">
                  {result.filename}
                </span>
                
                {result.success ? (
                  <span className="text-xs text-green-400 whitespace-nowrap">
                    Queued for processing
                  </span>
                ) : (
                  <span className="text-xs text-red-400 truncate">
                    {result.error}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
