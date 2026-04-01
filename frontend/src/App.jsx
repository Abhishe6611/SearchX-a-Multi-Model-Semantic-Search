import { useState, useCallback, useEffect } from 'react';
import { Upload, Search, Image, FileText, Database, CheckCircle, XCircle, Clock } from 'lucide-react';
import Header from './components/Header';
import UploadZone from './components/UploadZone';
import SearchBar from './components/SearchBar';
import FileGrid from './components/FileGrid';
import MediaViewer from './components/MediaViewer';
import StatsBar from './components/StatsBar';
import { getFiles, searchFiles, deleteFile, getStats } from './services/api';
import toast, { Toaster } from 'react-hot-toast';
import ConfirmModal from './components/ConfirmModal';

function App() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchMode, setSearchMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [stats, setStats] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  
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

  // Load files
  const loadFiles = useCallback(async (isBackground = false) => {
    try {
      if (!isBackground) setLoading(true);
      const response = await getFiles(0, 100);
      setFiles(response.files || []);
    } catch (error) {
      console.error('Failed to load files:', error);
    } finally {
      if (!isBackground) setLoading(false);
    }
  }, []);

  // Load stats
  const loadStats = useCallback(async () => {
    try {
      const response = await getStats();
      setStats(response.stats);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  }, []);

  // Search files
  const handleSearch = async (query) => {
    if (!query || query.trim() === '') {
      setSearchMode(false);
      setSearchQuery('');
      await loadFiles();
      return;
    }

    try {
      setLoading(true);
      setSearchMode(true);
      setSearchQuery(query);
      const response = await searchFiles(query);
      
      // Handle both success and error responses gracefully
      if (response && response.results) {
        setFiles(response.results);
      } else {
        console.error('Search returned unexpected format:', response);
        setFiles([]);
      }
    } catch (error) {
      console.error('Search failed:', error);
      setFiles([]);
      toast.error('Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Handle file deletion
  const handleDelete = async (fileId) => {
    const isConfirmed = await confirmAction('Are you sure you want to completely eradicate this file from the database?');
    if (!isConfirmed) return;

    try {
      await deleteFile(fileId);
      
      // Close viewer if deleted file was selected
      if (selectedFile && selectedFile.id === fileId) {
        setSelectedFile(null);
      }

      // Refresh files and stats
      if (searchMode) {
        await handleSearch(searchQuery);
      } else {
        await loadFiles();
      }
      await loadStats();
    } catch (error) {
      console.error('Delete failed:', error);
      toast.error('Failed to carefully delete file.');
    }
  };

  // Handle upload complete
  const handleUploadComplete = () => {
    setRefreshTrigger(prev => prev + 1);
    if (!searchMode) {
      loadFiles();
    }
    loadStats();
  };

  // Initial load
  useEffect(() => {
    loadFiles();
    loadStats();
  }, []);

  // Polling for status updates (separate from initial load)
  useEffect(() => {
    const interval = setInterval(() => {
      if (!searchMode) {
        loadFiles(true);
      }
      loadStats();
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(interval);
  }, [searchMode, loadFiles]);

  return (
    <div className="relative min-h-screen bg-aurora-bg overflow-hidden text-slate-200">
      <Toaster 
        position="top-center" 
        toastOptions={{ 
          style: { background: '#0f172a', color: '#cbd5e1', border: '1px solid rgba(255,255,255,0.1)' } 
        }} 
      />
      <ConfirmModal {...confirmConfig} />

      {/* Animated Background Mesh */}
      <div className="fixed inset-0 z-0 pointer-events-none w-full h-full overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[40vw] h-[40vw] rounded-full mix-blend-screen filter blur-[100px] opacity-30 bg-aurora-indigo animate-blob"></div>
        <div className="absolute top-[20%] right-[-10%] w-[35vw] h-[35vw] rounded-full mix-blend-screen filter blur-[120px] opacity-20 bg-aurora-cyan animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-[-20%] left-[20%] w-[45vw] h-[45vw] rounded-full mix-blend-screen filter blur-[130px] opacity-20 bg-aurora-violet animate-blob animation-delay-4000"></div>
      </div>

      <div className="relative z-10 w-full min-h-screen flex flex-col">
        <Header />
        
        <main className="container mx-auto px-4 py-4 flex-1">
          {/* Stats Bar */}
          {stats && <StatsBar stats={stats} />}

          {/* Upload Zone */}
          <UploadZone onUploadComplete={handleUploadComplete} />

          {/* Search Bar */}
          <SearchBar onSearch={handleSearch} searchMode={searchMode} />

          {/* Files Grid */}
          <FileGrid
            files={files}
            loading={loading}
            searchMode={searchMode}
            searchQuery={searchQuery}
            onFileClick={setSelectedFile}
            onDelete={handleDelete}
          />

          {/* Media Viewer Modal */}
          {selectedFile && (
            <MediaViewer
              file={selectedFile}
              onClose={() => setSelectedFile(null)}
              onDelete={handleDelete}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
