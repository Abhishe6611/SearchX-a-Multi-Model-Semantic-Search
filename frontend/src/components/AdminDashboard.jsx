import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getAllEmbeddings, getEmbeddingDetails, testSearchRanking, batchReprocessAllFiles, getReprocessStatus, reprocessSingleFile } from '../services/api';
import { Search, FileText, Database, TrendingUp, X, ChevronDown, ChevronUp, Home, ArrowLeft, RefreshCw, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import ConfirmModal from './ConfirmModal';

export default function AdminDashboard() {
  const [embeddings, setEmbeddings] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview'); // overview, search-test
  const [expandedFile, setExpandedFile] = useState(null);
  const [reprocessing, setReprocessing] = useState(false);
  const [reprocessSuccess, setReprocessSuccess] = useState(false);
  const [reprocessStatus, setReprocessStatus] = useState(null);
  const [reprocessingFileId, setReprocessingFileId] = useState(null);
  
  // Custom Confirm Modal State
  const [confirmConfig, setConfirmConfig] = useState({ isOpen: false, message: '', onConfirm: null, onCancel: null });

  // Awaitable Confirm UI Wrapper
  const confirmAction = (message) => new Promise((resolve) => {
    setConfirmConfig({
      isOpen: true,
      message,
      onConfirm: () => {
        setConfirmConfig({ isOpen: false, message: '', onConfirm: null, onCancel: null });
        resolve(true);
      },
      onCancel: () => {
        setConfirmConfig({ isOpen: false, message: '', onConfirm: null, onCancel: null });
        resolve(false);
      }
    });
  });

  useEffect(() => {
    let intervalId;
    if (reprocessing) {
      intervalId = setInterval(async () => {
        try {
          const status = await getReprocessStatus();
          setReprocessStatus(status);
          if (!status.is_running && status.total > 0 && status.completed + status.failed === status.total) {
            setReprocessing(false);
            setReprocessSuccess(true);
            setTimeout(() => setReprocessSuccess(false), 5000);
            loadEmbeddings();
          } else if (!status.is_running) {
            setReprocessing(false);
          }
        } catch (e) {
          console.error('Interval tracking lost contact with server:', e);
          setReprocessing(false);
        }
      }, 1000);
    }
    return () => clearInterval(intervalId);
  }, [reprocessing]);

  useEffect(() => {
    loadEmbeddings();
  }, []);

  const loadEmbeddings = async () => {
    try {
      setLoading(true);
      const data = await getAllEmbeddings();
      setEmbeddings(data.files || []);
    } catch (error) {
      console.error('Failed to load embeddings:', error);
    } finally {
      setLoading(false);
    }
  };

  const viewFileDetails = async (fileId) => {
    try {
      setLoading(true);
      const data = await getEmbeddingDetails(fileId);
      setSelectedFile(data.file);
    } catch (error) {
      console.error('Failed to load file details:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTestSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    try {
      setLoading(true);
      const data = await testSearchRanking(searchQuery, 20);
      setSearchResults(data);
      setActiveTab('search-test');
    } catch (error) {
      console.error('Search test failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (fileId) => {
    setExpandedFile(expandedFile === fileId ? null : fileId);
  };

  const handleReprocessAllFiles = async () => {
    const isConfirmed = await confirmAction('This will re-extract text and regenerate embeddings for ALL files. This is extremely heavy. Continue?');
    if (!isConfirmed) return;

    try {
      setReprocessing(true);
      setReprocessStatus(null);
      await batchReprocessAllFiles();
      // the polling effect will switch reprocessing to false when done
    } catch (error) {
      console.error('Reprocessing failed:', error);
      toast.error('Reprocessing failed: ' + (error.response?.data?.detail || error.message));
      setReprocessing(false);
    }
  };

  const handleReprocessSingle = async (e, fileId) => {
    e.stopPropagation();
    const isConfirmed = await confirmAction('Are you sure you want to regenerate indexing data for this specific file?');
    if (!isConfirmed) return;
    
    try {
      setReprocessingFileId(fileId);
      await reprocessSingleFile(fileId);
      
      // Start a dedicated polling loop just for this file
      const checkStatus = setInterval(async () => {
        try {
            const data = await getAllEmbeddings();
            const updatedFile = data.files.find(f => f.id === fileId);
            if (updatedFile && updatedFile.processing_status !== 'pending') {
               setEmbeddings(data.files || []);
               setReprocessingFileId(null);
               clearInterval(checkStatus);
               if (selectedFile?.id === fileId) {
                 viewFileDetails(fileId); // Refresh full Tensor details immediately
               }
            }
        } catch (err) {
            console.error(err);
        }
      }, 3000);
      
      // Cleanup safety net
      setTimeout(() => {
        clearInterval(checkStatus);
        setReprocessingFileId(prev => prev === fileId ? null : prev);
      }, 120000); // 2 minute maximum sync
      
    } catch (error) {
      console.error('Failed to reprocess file:', error);
      toast.error('Reprocessing failed: ' + (error.response?.data?.detail || error.message));
      setReprocessingFileId(null);
    }
  };

  const stats = {
    total: embeddings.length,
    withEmbeddings: embeddings.filter(f => f.has_embedding).length,
    withoutEmbeddings: embeddings.filter(f => !f.has_embedding).length,
    avgTextLength: embeddings.reduce((acc, f) => acc + (f.extracted_text_length || 0), 0) / embeddings.length || 0
  };

  return (
    <div className="min-h-screen bg-aurora-bg text-slate-200 relative overflow-hidden p-6 z-0">
      <ConfirmModal {...confirmConfig} />
      {/* Animated Background Mesh */}
      <div className="fixed inset-0 z-[-1] pointer-events-none w-full h-full overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[40vw] h-[40vw] rounded-full mix-blend-screen filter blur-[100px] opacity-20 bg-aurora-indigo animate-blob"></div>
        <div className="absolute bottom-[20%] right-[-10%] w-[35vw] h-[35vw] rounded-full mix-blend-screen filter blur-[120px] opacity-10 bg-aurora-cyan animate-blob animation-delay-2000"></div>
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-8">
            <Link
              to="/"
              className="flex items-center gap-2 px-4 py-2 bg-white/10 text-white border border-white/10 rounded-lg hover:bg-white/20 transition-all shadow-lg hover:shadow-aurora-cyan/20"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="font-medium">Back to SearchX</span>
            </Link>
            <Link
              to="/"
              className="flex items-center gap-2 text-aurora-cyan hover:text-cyan-300 transition-colors bg-aurora-cyan/10 px-4 py-2 rounded-full border border-aurora-cyan/20"
            >
              <Home className="w-4 h-4" />
              <span className="text-sm font-bold tracking-wide uppercase">Home</span>
            </Link>
          </div>
          <h1 className="text-4xl font-display font-bold text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-400 flex items-center gap-4">
            <div className="p-3 bg-aurora-indigo/20 rounded-2xl border border-aurora-indigo/30 shadow-[0_0_15px_rgba(79,70,229,0.3)]">
              <Database className="w-8 h-8 text-aurora-cyan" />
            </div>
            Admin Dashboard - Control Center
          </h1>
          <p className="text-slate-400 mt-3 font-medium text-lg">
            Manage embeddings, test search ranking algorithms, and oversee data synthesis.
          </p>

          {/* Reprocessing Tracker */}
          {(reprocessing || reprocessSuccess) && (
            <div className="mt-4 p-5 bg-slate-900/80 border border-white/10 rounded-xl shadow-lg">
               <div className="flex justify-between items-center mb-3">
                 <h3 className="font-bold text-white flex items-center gap-2">
                   {reprocessing ? <RefreshCw className="w-5 h-5 text-aurora-cyan animate-spin" /> : <div className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center text-slate-900 text-xs font-bold">✓</div>}
                   {reprocessing ? "Batch Reprocessing Running..." : "Batch Reprocessing Complete!"}
                 </h3>
                 {reprocessStatus && (
                   <span className="text-sm font-mono font-bold text-slate-300">
                     {reprocessStatus.completed} <span className="text-slate-500">/</span> {reprocessStatus.total} Media Parsed
                     {reprocessStatus.failed > 0 && <span className="text-rose-400 ml-3">({reprocessStatus.failed} failed)</span>}
                   </span>
                 )}
               </div>
               {reprocessStatus && (
                 <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden border border-white/5">
                   <div 
                     className="bg-gradient-to-r from-aurora-indigo to-aurora-cyan h-3 transition-all duration-500 rounded-full shadow-[0_0_10px_rgba(6,182,212,0.8)]" 
                     style={{ width: `${reprocessStatus.total > 0 ? Math.min(100, (reprocessStatus.completed + reprocessStatus.failed) / reprocessStatus.total * 100) : 0}%` }}
                   ></div>
                 </div>
               )}
               {reprocessSuccess && !reprocessing && (
                 <p className="text-sm text-slate-400 mt-3 font-medium">All files reprocessed. Lexicons and vector alignments have been renewed.</p>
               )}
            </div>
          )}
        </div>

        {/* Admin Actions */}
        <div className="glass-panel p-6 rounded-2xl shadow-xl mb-8 relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-r from-aurora-cyan/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
          <h2 className="text-lg font-display font-bold text-white mb-4 flex items-center gap-2 relative z-10">
            <RefreshCw className="w-6 h-6 text-aurora-cyan" />
            Operations Console
          </h2>
          <div className="flex gap-4 relative z-10">
            <button
              onClick={handleReprocessAllFiles}
              disabled={reprocessing || loading}
              className="px-6 py-3 bg-gradient-to-r from-rose-500 to-orange-500 text-white rounded-xl hover:shadow-[0_0_20px_rgba(244,63,94,0.4)] disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2 font-semibold border border-white/10 hover:scale-105"
            >
              {reprocessing ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  Processing Stack...
                </>
              ) : (
                <>
                  <RefreshCw className="w-5 h-5" />
                  Reprocess All Synthesis Data
                </>
              )}
            </button>
            <div className="flex-1 bg-slate-900/50 backdrop-blur-md p-4 rounded-xl border border-white/5 shadow-inner">
              <div className="flex gap-3">
                <AlertCircle className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-slate-300">
                  <p className="font-semibold text-white">Full re-extraction & embedding regeneration</p>
                  <p className="text-slate-400 mt-1 leading-relaxed">Runs the inference pipeline on all indexed files again for better search modeling accuracy. Heavy operation.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="glass-panel p-6 rounded-2xl shadow-lg border border-white/5 hover:-translate-y-1 transition-transform">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Total Files</div>
            <div className="text-4xl font-display font-bold text-white tracking-tight">{stats.total}</div>
          </div>
          <div className="glass-panel p-6 rounded-2xl shadow-lg border border-white/5 hover:-translate-y-1 transition-transform">
            <div className="text-xs font-bold uppercase tracking-wider text-green-400/80 mb-2 mt-0.5">With Embeddings</div>
            <div className="text-4xl font-display font-bold text-green-400 drop-shadow-[0_0_10px_rgba(74,222,128,0.3)] tracking-tight">{stats.withEmbeddings}</div>
          </div>
          <div className="glass-panel p-6 rounded-2xl shadow-lg border border-white/5 hover:-translate-y-1 transition-transform">
            <div className="text-xs font-bold uppercase tracking-wider text-orange-400/80 mb-2 mt-0.5">Missing Embeddings</div>
            <div className="text-4xl font-display font-bold text-orange-400 drop-shadow-[0_0_10px_rgba(251,146,60,0.3)] tracking-tight">{stats.withoutEmbeddings}</div>
          </div>
          <div className="glass-panel p-6 rounded-2xl shadow-lg border border-white/5 hover:-translate-y-1 transition-transform">
            <div className="text-xs font-bold uppercase tracking-wider text-aurora-cyan/80 mb-2 mt-0.5">Avg Text Length</div>
            <div className="text-4xl font-display font-bold text-aurora-cyan drop-shadow-[0_0_10px_rgba(6,182,212,0.3)] tracking-tight">{Math.round(stats.avgTextLength)}</div>
          </div>
        </div>

        {/* Search Test Section */}
        <div className="glass-panel p-6 rounded-2xl shadow-xl mb-8 border border-white/5">
          <h2 className="text-xl font-display font-bold text-white mb-4 flex items-center gap-2">
            <Search className="w-6 h-6 text-aurora-cyan" />
            Test Search Ranking
          </h2>
          <form onSubmit={handleTestSearch} className="flex gap-4">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Enter search query to test algorithmic ranking..."
              className="flex-1 px-4 py-3 bg-slate-900/50 border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-aurora-cyan/50 text-white placeholder-slate-400"
            />
            <button
              type="submit"
              disabled={loading || !searchQuery.trim()}
              className="px-6 py-3 bg-aurora-cyan/20 text-aurora-cyan border border-aurora-cyan/30 rounded-xl hover:bg-aurora-cyan hover:text-slate-900 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-bold transition-all shadow-[0_0_15px_rgba(6,182,212,0.1)]"
            >
              <TrendingUp className="w-5 h-5" />
              Test Ranking
            </button>
          </form>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 mb-6 relative z-10">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-6 py-3 font-semibold rounded-xl transition-all border ${
              activeTab === 'overview'
                ? 'bg-aurora-indigo/30 text-white border-aurora-indigo/50 shadow-[0_0_15px_rgba(79,70,229,0.3)]'
                : 'glass-panel text-slate-400 border-white/5 hover:text-white hover:bg-white/5'
            }`}
          >
            All Files Overview
          </button>
          <button
            onClick={() => setActiveTab('search-test')}
            className={`px-6 py-3 font-semibold rounded-xl transition-all border ${
              activeTab === 'search-test'
                ? 'bg-aurora-cyan/20 text-aurora-cyan border-aurora-cyan/50 shadow-[0_0_15px_rgba(6,182,212,0.3)]'
                : 'glass-panel text-slate-400 border-white/5 hover:text-white hover:bg-white/5'
            }`}
          >
            Search Test Results
            {searchResults && (
              <span className="ml-2 px-2 py-0.5 text-xs bg-aurora-cyan text-slate-900 font-bold rounded-full">
                {searchResults.count}
              </span>
            )}
          </button>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-4 relative z-10">
            {loading && embeddings.length === 0 ? (
              <div className="text-center py-12 text-slate-400 font-medium tracking-wide">Scanning Neural Database...</div>
            ) : embeddings.length === 0 ? (
              <div className="text-center py-12 text-slate-400 font-medium tracking-wide">No files found within vector index.</div>
            ) : (
              embeddings.map((file) => (
                <div key={file.id} className="glass-panel rounded-2xl shadow-lg border border-white/5 overflow-hidden transition-all hover:border-white/10 group">
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          <h3 className="text-lg font-bold text-white tracking-wide">{file.original_filename}</h3>
                          <span className={`px-3 py-1 rounded-full text-xs font-bold tracking-wider uppercase border ${
                            file.processing_status === 'success' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                            file.processing_status === 'failed' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                            'bg-orange-500/10 text-orange-400 border-orange-500/20'
                          }`}>
                            {file.processing_status}
                          </span>
                          {file.has_embedding && (
                            <span className="px-3 py-1 rounded-full text-xs font-bold tracking-wider uppercase bg-aurora-cyan/10 text-aurora-cyan border border-aurora-cyan/20 drop-shadow-[0_0_8px_rgba(6,182,212,0.3)]">
                              ✓ EMBEDDED
                            </span>
                          )}
                        </div>
                        <div className="flex gap-6 text-sm text-slate-400 font-medium">
                          <span>Format: <span className="text-slate-300">{file.file_type}</span></span>
                          <span>Size: <span className="text-slate-300">{(file.file_size / 1024).toFixed(1)} KB</span></span>
                          <span>Text Volume: <span className="text-slate-300">{file.extracted_text_length} chars</span></span>
                          {file.embedding_id !== null && (
                            <span>Text ID: <span className="text-slate-300 font-mono">{file.embedding_id}</span></span>
                          )}
                           {file.image_embedding_id !== null && (
                            <span>Image ID: <span className="text-slate-300 font-mono">{file.image_embedding_id}</span></span>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={() => toggleExpand(file.id)}
                        className="p-2 bg-white/5 hover:bg-white/10 border border-white/5 rounded-xl transition-colors text-slate-300"
                      >
                        {expandedFile === file.id ? (
                          <ChevronUp className="w-5 h-5" />
                        ) : (
                          <ChevronDown className="w-5 h-5" />
                        )}
                      </button>
                    </div>

                    {expandedFile === file.id && (
                      <div className="border-t border-white/10 pt-4 mt-4">
                        <div className="mb-4">
                          <h4 className="font-semibold text-slate-300 mb-2 text-sm uppercase tracking-wider">Extracted Optical Data:</h4>
                          <div className="bg-slate-900/50 border border-white/5 p-4 rounded-xl max-h-48 overflow-y-auto custom-scrollbar">
                            <pre className="text-sm text-slate-400 whitespace-pre-wrap font-mono leading-relaxed">
                              {file.extracted_text ? (
                                file.extracted_text.substring(0, 1000) + (file.extracted_text.length > 1000 ? '...' : '')
                              ) : (
                                <span className="text-slate-500 italic uppercase">No Text Extracted</span>
                              )}
                            </pre>
                          </div>
                        </div>
                        <div className="flex gap-4">
                          <button
                            onClick={() => viewFileDetails(file.id)}
                            className="px-5 py-2.5 bg-aurora-indigo/20 text-indigo-300 border border-aurora-indigo/30 rounded-xl hover:bg-aurora-indigo/40 transition-colors flex items-center gap-2 font-bold hover:shadow-[0_0_15px_rgba(79,70,229,0.2)]"
                          >
                            <FileText className="w-4 h-4" />
                            Inspect Artificial Tensors
                          </button>
                          <button
                            onClick={(e) => handleReprocessSingle(e, file.id)}
                            disabled={reprocessingFileId === file.id || reprocessing}
                            className="px-5 py-2.5 bg-rose-500/20 text-rose-300 border border-rose-500/30 rounded-xl hover:bg-rose-500/40 transition-colors flex items-center gap-2 font-bold focus:outline-none hover:shadow-[0_0_15px_rgba(244,63,94,0.2)] disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {reprocessingFileId === file.id ? (
                              <><RefreshCw className="w-4 h-4 animate-spin" /> Re-parsing...</>
                            ) : (
                              <><RefreshCw className="w-4 h-4" /> Reprocess Document</>
                            )}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Search Test Tab */}
        {activeTab === 'search-test' && searchResults && (
          <div className="space-y-4 relative z-10">
            {/* Search Overview Stats */}
            <div className="glass-panel p-6 rounded-2xl shadow-lg border border-white/5 bg-gradient-to-br from-slate-900/80 to-transparent">
              <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <Search className="w-5 h-5 text-aurora-cyan" />
                Algorithm Diagnostics
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-slate-400 font-medium">Semantic Query</div>
                  <div className="font-bold text-white mt-1">"{searchResults.query}"</div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 font-medium">Nodes Recovered</div>
                  <div className="font-display font-bold text-aurora-cyan text-xl mt-1">{searchResults.count}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 font-medium">Model Architecture</div>
                  <div className="font-semibold text-white mt-1 text-xs uppercase tracking-wide">{searchResults.index_info?.model?.split('/').pop() || 'DUAL (CLIP+MPNet)'}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 font-medium">Dimension Pool</div>
                  <div className="font-bold text-white mt-1">{searchResults.index_info?.total_vectors || 'READY'}</div>
                </div>
              </div>
            </div>

            {searchResults.results.map((result, index) => (
              <div key={result.id} className="glass-panel rounded-2xl shadow-lg border border-white/5 overflow-hidden transition-all hover:border-white/20">
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-4">
                      {/* Rank Badge */}
                      <div className={`flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center font-display font-bold text-xl ${
                        index === 0 ? 'bg-gradient-to-br from-amber-400/20 to-orange-500/20 border border-amber-400/30' : 
                        index === 1 ? 'bg-gradient-to-br from-slate-300/20 to-slate-400/20 border border-slate-300/30 text-white': 
                        index === 2 ? 'bg-gradient-to-br from-amber-700/20 to-amber-800/20 border border-amber-700/30 text-white' : 
                        'bg-white/5 border border-white/10 text-slate-400' 
                      }`}>
                        <span className={index === 0 ? "bg-clip-text text-transparent bg-gradient-to-b from-amber-200 to-amber-500 font-extrabold" : ""}>#{index + 1}</span>
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-white tracking-wide">{result.original_filename}</h3>
                        <div className="flex gap-4 text-sm text-slate-400 font-medium mt-1">
                          <span>Format: <span className="text-slate-300">{result.file_type}</span></span>
                          <span>Text Volume: <span className="text-slate-300">{result.extracted_text_length} chars</span></span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-3xl font-display font-bold text-aurora-cyan drop-shadow-[0_0_8px_rgba(6,182,212,0.4)]">
                        {result.relevance_percentage}%
                      </div>
                      <div className="text-xs text-slate-400 font-bold tracking-wider uppercase mt-1">Cosine Correlation</div>
                      <div className="text-xs text-slate-500 mt-1 font-mono tracking-tighter">Tensor Map: {result.relevance_score.toFixed(4)}</div>
                    </div>
                  </div>

                  {result.keywords && result.keywords.length > 0 && (
                    <div className="mb-4">
                      <h4 className="font-semibold text-slate-300 mb-2 text-xs uppercase tracking-wider">Computed Lexicon:</h4>
                      <div className="flex flex-wrap gap-2">
                        {result.keywords.map((keyword, i) => (
                          <span key={i} className="px-3 py-1 bg-white/5 border border-white/10 text-aurora-cyan rounded-full text-xs font-bold tracking-wide">
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="border-t border-white/10 pt-4">
                    <h4 className="font-semibold text-slate-300 mb-2 text-xs uppercase tracking-wider">Semantic Trace:</h4>
                    <div className="bg-slate-900/50 border border-white/5 p-4 rounded-xl max-h-48 overflow-y-auto custom-scrollbar">
                      <pre className="text-xs text-slate-400 whitespace-pre-wrap font-mono leading-relaxed">
                        {result.extracted_text ? (
                          result.extracted_text.substring(0, 500) + (result.extracted_text.length > 500 ? '...' : '')
                        ) : (
                          <span className="text-slate-500 italic uppercase">Vector relies completely on visual parameters. No text extracted.</span>
                        )}
                      </pre>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty Search Tab State */}
        {activeTab === 'search-test' && !searchResults && (
          <div className="glass-panel p-16 rounded-2xl shadow border border-white/5 text-center text-slate-400 relative z-10 flex flex-col items-center justify-center">
            <div className="p-5 bg-white/5 rounded-full mb-6 relative">
              <Search className="w-12 h-12 text-aurora-cyan/60" />
              <div className="absolute inset-0 border border-aurora-cyan/30 rounded-full animate-ping"></div>
            </div>
            <p className="text-xl font-display font-bold text-white mb-2">Awaiting Input Signal</p>
            <p>Execute a search query above to inspect mathematical similarities.</p>
          </div>
        )}

        {/* Deep Dive File Details Modal */}
        {selectedFile && (
          <div className="fixed inset-0 bg-slate-900/80 backdrop-blur-md flex items-center justify-center p-6 z-50">
            <div className="glass-panel border border-aurora-cyan/20 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto custom-scrollbar relative">
              {/* Modal Header */}
              <div className="p-6 border-b border-white/10 flex items-start justify-between sticky top-0 bg-slate-900/80 backdrop-blur-xl z-20">
                <div>
                  <h2 className="text-2xl font-display font-bold text-white tracking-wide">{selectedFile.original_filename}</h2>
                  <p className="text-aurora-cyan font-mono text-sm mt-1 uppercase tracking-widest">NODE_ID: {selectedFile.id}</p>
                </div>
                <button
                  onClick={() => setSelectedFile(null)}
                  className="p-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-colors text-slate-300 hover:text-white"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="p-6 space-y-8">
                {/* Embedding Stats */}
                {selectedFile.embedding_stats && (
                  <div>
                    <h3 className="font-bold text-white mb-3 text-lg flex items-center gap-2 tracking-wide">
                      <Database className="w-5 h-5 text-aurora-indigo" />
                      Tensor Topology
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 bg-slate-900/50 border border-white/5 p-5 rounded-xl">
                      <div>
                        <div className="text-xs text-slate-400 font-bold uppercase tracking-wider">Dimension Space</div>
                        <div className="font-display font-bold text-white text-xl mt-1">{selectedFile.embedding_stats.dimension}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-400 font-bold uppercase tracking-wider">Calculated Norm</div>
                        <div className="font-display font-bold text-white text-xl mt-1">{selectedFile.embedding_stats.norm.toFixed(4)}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-400 font-bold uppercase tracking-wider">Median Slice</div>
                        <div className="font-display font-bold text-white text-xl mt-1">{selectedFile.embedding_stats.mean.toFixed(4)}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-400 font-bold uppercase tracking-wider">Std Deviation</div>
                        <div className="font-display font-bold text-white text-xl mt-1">{selectedFile.embedding_stats.std.toFixed(4)}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-400 font-bold uppercase tracking-wider">Min Float</div>
                        <div className="font-display font-bold text-white text-xl mt-1">{selectedFile.embedding_stats.min.toFixed(4)}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-400 font-bold uppercase tracking-wider">Max Float</div>
                        <div className="font-display font-bold text-white text-xl mt-1">{selectedFile.embedding_stats.max.toFixed(4)}</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Keywords */}
                {selectedFile.keywords && selectedFile.keywords.length > 0 && (
                  <div>
                    <h3 className="font-bold text-white mb-3 text-lg tracking-wide">Lexicon Frequency (Top 20)</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedFile.keywords.map((item, i) => (
                        <span key={i} className="px-3 py-2 bg-aurora-indigo/10 border border-aurora-indigo/20 text-indigo-300 rounded-xl text-sm">
                          <span className="font-bold">{item.word}</span>
                          <span className="text-indigo-400/50 ml-2 font-mono text-xs">f={item.count}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Full Extracted Text */}
                <div>
                  <h3 className="font-bold text-white mb-3 text-lg tracking-wide">Optical Payload Stream</h3>
                  <div className="bg-slate-900/50 border border-white/5 p-5 rounded-xl max-h-96 overflow-y-auto custom-scrollbar">
                    <pre className="text-sm text-slate-300 whitespace-pre-wrap font-mono leading-relaxed">
                      {selectedFile.extracted_text || <span className="text-slate-500 italic line-through tracking-wider">NULL TEXT POINTER. PURE VISUAL ASSET.</span>}
                    </pre>
                  </div>
                  <div className="text-xs text-slate-400 font-mono mt-3 text-right">
                    BUFFER_LEN: {selectedFile.extracted_text_length} chars
                  </div>
                </div>

                {/* Embedding Vector (collapsed by default) */}
                {selectedFile.embedding_vector && (
                  <details className="group">
                    <summary className="font-bold text-sm text-aurora-cyan mb-3 cursor-pointer hover:text-cyan-300 transition-colors flex items-center gap-2 outline-none uppercase tracking-wider">
                      <ChevronDown className="w-5 h-5 group-open:-rotate-180 transition-transform" />
                      Decompile Raw Tensor (Float Array Matrix)
                    </summary>
                    <div className="bg-[#0a0a0f] border border-white/10 p-5 rounded-xl max-h-64 overflow-y-auto custom-scrollbar mt-4">
                      <pre className="text-xs text-aurora-cyan font-mono opacity-80">
                        {JSON.stringify(selectedFile.embedding_vector, null, 2)}
                      </pre>
                    </div>
                  </details>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
