import React from 'react';
import { AlertCircle, X, Check } from 'lucide-react';

export default function ConfirmModal({ isOpen, message, onConfirm, onCancel }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-900/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900/90 border border-white/10 rounded-2xl shadow-2xl p-6 max-w-md w-full animate-in zoom-in-95 duration-200">
        <div className="flex items-start gap-4 mb-6">
          <div className="p-3 bg-aurora-cyan/10 rounded-full border border-aurora-cyan/20 shrink-0">
            <AlertCircle className="w-6 h-6 text-aurora-cyan" />
          </div>
          <div>
            <h3 className="text-xl font-display font-bold text-white mb-2">Confirmation Required</h3>
            <p className="text-slate-300 leading-relaxed font-medium">{message}</p>
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-8">
          <button
            onClick={onCancel}
            className="px-5 py-2.5 bg-white/5 hover:bg-white/10 text-slate-300 font-bold rounded-xl border border-white/10 transition-colors flex items-center gap-2"
          >
            <X className="w-4 h-4" /> Cancel
          </button>
          <button
            onClick={onConfirm}
            className="px-5 py-2.5 bg-aurora-cyan/20 hover:bg-aurora-cyan/40 text-aurora-cyan font-bold rounded-xl border border-aurora-cyan/30 transition-all hover:shadow-[0_0_15px_rgba(6,182,212,0.3)] flex items-center gap-2 outline-none focus:ring-2 focus:ring-aurora-cyan/50 focus:ring-offset-2 focus:ring-offset-slate-900"
          >
            <Check className="w-4 h-4" /> Confirm Action
          </button>
        </div>
      </div>
    </div>
  );
}
