export default function ReportSummary({ report }) {
  if (!report) return null;

  const qualityScore = Math.round(report.overall_quality_score);
  const qualityStatus = qualityScore >= 85 ? 'Excellent' : qualityScore >= 70 ? 'Good' : qualityScore >= 50 ? 'Fair' : 'Needs Work';
  const statusColor = qualityScore >= 85 ? 'text-green-600' : qualityScore >= 70 ? 'text-blue-600' : qualityScore >= 50 ? 'text-amber-600' : 'text-red-600';
  const bgColor = qualityScore >= 85 ? 'from-green-50 to-emerald-50 border-green-200' : qualityScore >= 70 ? 'from-blue-50 to-sky-50 border-blue-200' : qualityScore >= 50 ? 'from-amber-50 to-yellow-50 border-amber-200' : 'from-red-50 to-rose-50 border-red-200';

  const metrics = [
    { label: "Records", value: report.records, icon: "📊", color: "sky" },
    { label: "Columns", value: report.total_columns, icon: "📋", color: "sky" },
    { label: "Quality", value: `${qualityScore}%`, icon: "⭐", highlight: true },
    { label: "Missing", value: report.missing_fields, icon: "❌", color: "red" },
    { label: "Invalid", value: report.invalid_fields, icon: "⚠️", color: "amber" },
    { label: "Duplicates", value: report.duplicate_rows, icon: "🔄", color: "purple" },
  ];

  return (
    <div className="space-y-6">
      {/* Quality Score Banner */}
      <div className={`bg-gradient-to-r ${bgColor} border-2 rounded-xl p-8 shadow-sm hover:shadow-md transition-shadow`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-gray-600 mb-2">📈 Overall Quality Score</p>
            <div className="flex items-end gap-3">
              <p className={`text-5xl font-black ${statusColor}`}>{qualityScore}%</p>
              <p className={`text-lg font-semibold ${statusColor} mb-2`}>{qualityStatus}</p>
            </div>
            <div className="mt-3 h-2 bg-gray-200 rounded-full overflow-hidden w-48">
              <div 
                className={`h-full rounded-full transition-all duration-500 ${
                  qualityScore >= 85 ? 'bg-green-600' : 
                  qualityScore >= 70 ? 'bg-blue-600' : 
                  qualityScore >= 50 ? 'bg-amber-600' : 'bg-red-600'
                }`}
                style={{ width: `${qualityScore}%` }}
              />
            </div>
          </div>
          <div className="text-7xl animate-bounce">
            {qualityScore >= 85 ? '🎉' : qualityScore >= 70 ? '👍' : qualityScore >= 50 ? '🤔' : '😟'}
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {metrics.map((m, idx) => (
          <div
            key={m.label}
            className={`rounded-xl p-5 text-center transition-all duration-300 transform hover:scale-105 ${
              m.highlight
                ? 'bg-gradient-to-br from-sky-100 to-sky-50 border-2 border-sky-400 shadow-lg scale-105'
                : 'bg-gray-50 border border-gray-200 hover:border-gray-300 hover:shadow-md'
            }`}
            style={{
              animation: `slideIn 0.5s ease-out ${idx * 0.05}s both`
            }}
          >
            <span className="text-3xl block mb-2">{m.icon}</span>
            <p className="text-2xl font-black text-gray-900">{m.value}</p>
            <p className="text-xs font-bold text-gray-600 mt-2 uppercase tracking-wide">{m.label}</p>
          </div>
        ))}
      </div>

      {/* All Fields Breakdown */}
      {report.all_columns && report.all_columns.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">📊 Field Analysis</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
            {report.all_columns.map((col) => {
              const missing = report.missing_per_column[col] || 0;
              const completeness = Math.round(((report.records - missing) / report.records) * 100);
              return (
                <div key={col} className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
                  <p className="font-semibold text-gray-900 truncate">{col}</p>
                  <div className="mt-2 flex items-center justify-between text-sm">
                    <span className={completeness === 100 ? 'text-green-600' : completeness >= 80 ? 'text-amber-600' : 'text-red-600'}>
                      {completeness}%
                    </span>
                    <span className="text-gray-600">{missing} missing</span>
                  </div>
                  <div className="mt-2 h-1.5 bg-gray-300 rounded-full overflow-hidden">
                    <div
                      className={completeness === 100 ? 'bg-green-500' : completeness >= 80 ? 'bg-amber-500' : 'bg-red-500'}
                      style={{ width: `${completeness}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <style>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(10px);
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
