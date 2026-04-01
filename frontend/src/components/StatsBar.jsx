import { Database, CheckCircle, XCircle, Clock, Image, FileText } from 'lucide-react';

export default function StatsBar({ stats }) {
  if (!stats) return null;

  const statItems = [
    {
      icon: Database,
      label: 'Total Files',
      value: stats.total_files,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10'
    },
    {
      icon: CheckCircle,
      label: 'Processed',
      value: stats.processed,
      color: 'text-green-400',
      bgColor: 'bg-green-500/10'
    },
    {
      icon: Clock,
      label: 'Processing',
      value: stats.pending,
      color: 'text-orange-400',
      bgColor: 'bg-orange-500/10'
    },
    {
      icon: XCircle,
      label: 'Failed',
      value: stats.failed,
      color: 'text-red-400',
      bgColor: 'bg-red-500/10'
    },
    {
      icon: Image,
      label: 'Images',
      value: stats.images,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/10'
    },
    {
      icon: FileText,
      label: 'Documents',
      value: stats.documents,
      color: 'text-cyan-400',
      bgColor: 'bg-cyan-500/10'
    }
  ];

  return (
    <div className="mb-6">
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {statItems.map((item, index) => {
          const Icon = item.icon;
          
          return (
            <div
              key={index}
              className="group glass-panel rounded-xl p-3 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgba(0,0,0,0.4)] hover:border-white/10 transition-all duration-300 relative overflow-hidden"
            >
              {/* Subtle background glow on hover */}
              <div className="absolute -inset-2 bg-gradient-to-r from-transparent via-white/5 to-transparent opacity-0 group-hover:opacity-100 blur-xl transition-opacity duration-500"></div>
              
              <div className="relative flex flex-col gap-3">
                <div className={`self-start p-2 rounded-lg bg-slate-900/50 border border-white/5 backdrop-blur-md shadow-inner group-hover:scale-110 transition-transform duration-300`}>
                  <Icon className={`w-4 h-4 ${item.color} drop-shadow-[0_0_8px_currentColor]`} />
                </div>
                
                <div className="flex-1 min-w-0">
                  <p className="text-xl font-display font-bold text-white tracking-tight">
                    {item.value}
                  </p>
                  <p className="text-[10px] font-medium text-slate-400 mt-0.5 uppercase tracking-wider">
                    {item.label}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
