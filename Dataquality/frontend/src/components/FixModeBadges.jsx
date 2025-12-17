export default function FixModeBadges({ report }) {
  if (!report) return null;

  const totalFixes = report.offline_fixes + report.online_fixes + report.manual_review;
  const offlineRatio = totalFixes === 0 ? 0 : (report.offline_fixes / totalFixes) * 100;

  const badges = [
    {
      icon: "✅",
      label: "Offline",
      value: report.offline_fixes,
      sublabel: "Auto-fixed",
      color: "from-green-50 to-emerald-50 border-green-300 text-green-700",
      accentColor: "text-green-600"
    },
    {
      icon: "🌐",
      label: "Online",
      value: report.online_fixes,
      sublabel: "Escalated",
      color: "from-blue-50 to-sky-50 border-blue-300 text-blue-700",
      accentColor: "text-blue-600"
    },
    {
      icon: "👤",
      label: "Manual",
      value: report.manual_review,
      sublabel: "To review",
      color: "from-amber-50 to-yellow-50 border-amber-300 text-amber-700",
      accentColor: "text-amber-600"
    },
    {
      icon: "📊",
      label: "Ratio",
      value: `${offlineRatio.toFixed(0)}%`,
      sublabel: "Offline-first",
      color: "from-purple-50 to-pink-50 border-purple-300 text-purple-700",
      accentColor: "text-purple-600"
    }
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      {badges.map((badge, idx) => (
        <div
          key={badge.label}
          className={`bg-gradient-to-br ${badge.color} border-2 rounded-xl p-6 transition-all duration-300 transform hover:scale-105 hover:shadow-lg`}
          style={{
            animation: `slideInUp 0.5s ease-out ${idx * 0.1}s both`
          }}
        >
          <div className="flex items-start justify-between mb-3">
            <span className="text-3xl">{badge.icon}</span>
            <span className={`text-xs font-black uppercase tracking-widest ${badge.accentColor}`}>
              {badge.label}
            </span>
          </div>
          <p className={`text-4xl font-black ${badge.accentColor} mb-2`}>
            {badge.value}
          </p>
          <p className={`text-xs font-semibold ${badge.accentColor} opacity-75`}>
            {badge.sublabel}
          </p>
        </div>
      ))}

      <style>{`
        @keyframes slideInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}
