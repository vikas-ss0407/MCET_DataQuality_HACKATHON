import React, { useState } from "react";
import axios from "axios";
import UploadForm from "./components/UploadForm.jsx";
import ReportSummary from "./components/ReportSummary.jsx";
import FixModeBadges from "./components/FixModeBadges.jsx";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export default function App() {
  const [report, setReport] = useState(null);
  const [cleanedData, setCleanedData] = useState([]);
  const [fixes, setFixes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [verifyingIndex, setVerifyingIndex] = useState(null);
  const [aiSuggestIndex, setAiSuggestIndex] = useState(null);

  const handleUpload = async (file) => {
    setError(null);
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await axios.post(`${API_BASE}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setReport(response.data.report);
      setCleanedData(response.data.cleaned_data || []);
      setFixes(response.data.fixes || []);
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      const resp = await axios.get(`${API_BASE}/download/cleaned`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([resp.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "cleaned_data.csv");
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (err) {
      setError("No cleaned dataset yet. Upload first.");
    }
  };

  const handleDownloadExcel = async () => {
    try {
      const resp = await axios.get(`${API_BASE}/download/excel`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([resp.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "data_quality_report.xlsx");
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
    } catch (err) {
      setError("No report available yet. Upload first.");
    }
  };

  const handleAiSuggest = async (fixIndex, field, value) => {
    setAiSuggestIndex(fixIndex);
    try {
      const response = await axios.post(`${API_BASE}/ai-suggest`, {
        field_type: field,
        value: value ?? "",
      });

      const updatedFixes = [...fixes];
      updatedFixes[fixIndex] = {
        ...updatedFixes[fixIndex],
        suggested: response.data.suggestion,
        confidence: response.data.confidence,
        processing_mode: response.data.source,
        note: response.data.details,
        // Mark verified only when confidence is high
        verified_online: Number(response.data.confidence || 0) >= 0.8,
      };
      setFixes(updatedFixes);
    } catch (err) {
      setError(`AI suggestion failed: ${err.message}`);
    } finally {
      setAiSuggestIndex(null);
    }
  };

  const handleVerifyOnline = async (fixIndex, field, value) => {
    setVerifyingIndex(fixIndex);
    try {
      // Determine field type based on field name
      let fieldType = "email";
      if (field.toLowerCase().includes("phone")) {
        fieldType = "phone";
      }

      const response = await axios.post(`${API_BASE}/verify-online`, {
        field_type: fieldType,
        value: value,
      });

      // Update the fix with online verification result
      const updatedFixes = [...fixes];
      updatedFixes[fixIndex] = {
        ...updatedFixes[fixIndex],
        suggested: response.data.suggestion,
        confidence: response.data.confidence,
        processing_mode: response.data.source,
        note: response.data.details,
        verified_online: true,
      };
      setFixes(updatedFixes);
    } catch (err) {
      setError(`Online verification failed: ${err.message}`);
    } finally {
      setVerifyingIndex(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Hero Section */}
      <header className="bg-gradient-to-r from-sky-600 to-sky-800 text-white">
        <div className="max-w-7xl mx-auto px-6 py-12 flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-widest text-sky-100 mb-2">
              🛡️ Data Quality Platform
            </p>
            <h1 className="text-4xl font-bold mb-3">Offline-First QA Guardian</h1>
            <p className="text-lg text-sky-50 max-w-lg">
              Upload CSV or Excel files, run offline validation, and download cleaned data with transparent reports.
            </p>
          </div>
          <div className="bg-sky-500 bg-opacity-20 border border-sky-300 rounded-lg px-6 py-4 text-right">
            <span className="text-sm font-semibold">✨ AI-Powered</span>
            <p className="text-xs text-sky-100 mt-1">Enhanced Data Quality</p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Upload Card */}
          <div className="bg-white rounded-xl shadow-md border border-gray-100 p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-sky-100 rounded-lg flex items-center justify-center text-sky-600 font-bold">
                1
              </div>
              <h2 className="text-2xl font-bold text-gray-900">Upload File</h2>
            </div>
            <UploadForm onUpload={handleUpload} loading={loading} />
            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-700 font-medium">⚠️ Error</p>
                <p className="text-sm text-red-600 mt-1">{error}</p>
              </div>
            )}
            {report && (
              <div className="space-y-3 mt-6">
                <button
                  onClick={handleDownload}
                  className="w-full px-6 py-3 bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded-lg transition-all duration-200 shadow-md hover:shadow-lg"
                >
                  ⬇️ Download CSV (Original Data)
                </button>
                <button
                  onClick={handleDownloadExcel}
                  className="w-full px-6 py-3 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition-all duration-200 shadow-md hover:shadow-lg"
                >
                  📊 Download Excel (with Missing/Invalid/Duplicates)
                </button>
              </div>
            )}
          </div>

          {/* QA Report Card */}
          <div className="bg-white rounded-xl shadow-md border border-gray-100 p-8 lg:col-span-2">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center text-green-600 font-bold">
                2
              </div>
              <h2 className="text-2xl font-bold text-gray-900">QA Report</h2>
            </div>
            {report ? (
              <div className="space-y-6">
                <ReportSummary report={report} />
                <FixModeBadges report={report} />
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-500 text-lg">📊 Upload a file to see the QA report</p>
              </div>
            )}
          </div>
        </div>

        {/* Fix Log Card */}
        {fixes.length > 0 && (
          <div className="bg-white rounded-xl shadow-md border border-gray-100 p-8 mt-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center text-amber-600 font-bold">
                3
              </div>
              <h2 className="text-2xl font-bold text-gray-900">Fix Log</h2>
              <span className="ml-auto inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-amber-50 text-amber-700 border border-amber-200">{fixes.length} fixes applied</span>
            </div>

            {/* Online Verification Info Banner */}
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-start gap-3">
                <span className="text-2xl">💡</span>
                <div>
                  <h3 className="font-semibold text-blue-900 mb-1">Online Verification Available</h3>
                  <p className="text-sm text-blue-700">
                    For items marked as <span className="font-semibold">MANUAL</span> or <span className="font-semibold">ONLINE</span>, 
                    click <span className="font-semibold">"🌐 Verify Online"</span> to use real-time API validation for higher accuracy.
                  </p>
                </div>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700 w-24">Mode</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700 w-32">Field</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700 flex-1">Change</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700 w-20">Confidence</th><th className="text-left py-3 px-4 font-semibold text-gray-700">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {fixes.slice(0, 50).map((fix, idx) => {
                    const mode = String(fix.processing_mode || '').toLowerCase();
                    const modeClasses =
                      mode === 'accept'
                        ? 'bg-green-50 text-green-700 border border-green-200'
                        : mode === 'suggest'
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : mode === 'manual'
                        ? 'bg-red-50 text-red-700 border border-red-200'
                        : 'bg-gray-100 text-gray-700 border border-gray-200';
                    
                    const needsOnlineVerification = 
                      (mode === 'manual' && fix.confidence < 0.6) || 
                      (fix.processing_mode === 'ONLINE' && !fix.verified_online) ||
                      (fix.processing_mode === 'MANUAL' && !fix.verified_online);
                    
                    const canVerifyOnline = 
                      fix.field.toLowerCase().includes('email') || 
                      fix.field.toLowerCase().includes('phone');

                    // Only show AI Suggest for rows that truly need it:
                    // - Mode is MANUAL or ONLINE
                    // - Confidence is low (< 0.8)
                    const canAiSuggest = (
                      fix.field.toLowerCase().includes('email') ||
                      fix.field.toLowerCase().includes('phone') ||
                      fix.field.toLowerCase().includes('name') ||
                      fix.field.toLowerCase().includes('job') ||
                      fix.field.toLowerCase() === 'id'
                    );
                    // Rows that explicitly require manual review should not show AI Suggest
                    const isManualOnly = (
                      String(fix.suggested || '').trim().startsWith('[') ||
                      String(fix.note || '').toLowerCase().includes('manual review') ||
                      String(fix.processing_mode || '').toLowerCase() === 'manual' && Number(fix.confidence || 0) === 0
                    );
                    // Allow AI suggest for manual/online items, and also low-confidence offline names
                    const needsAiSuggest = (
                      (
                        mode === 'manual' ||
                        mode === 'online' ||
                        (mode === 'offline' && Number(fix.confidence || 0) < 0.8 && canAiSuggest)
                      ) &&
                      Number(fix.confidence || 0) < 0.8 &&
                      !fix.verified_online &&
                      canAiSuggest &&
                      !isManualOnly
                    );

                    return (
                      <tr key={`${fix.field}-${fix.row_index}-${idx}`} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <span className={`inline-flex items-center px-2 py-1 text-xs font-bold rounded-full ${modeClasses}`}>
                            {fix.verified_online ? '🌐 ' + fix.processing_mode : fix.processing_mode}
                          </span>
                        </td>
                      <td className="py-3 px-4 font-medium text-gray-900">{fix.field}</td>
                      <td className="py-3 px-4 text-gray-700">
                        <span className="text-gray-400">"{fix.original || "(empty)"}"</span>
                        {' → '}
                        <span className="text-green-700 font-medium">"{fix.suggested || "(empty)"}"</span>
                      </td>
                      <td className="py-3 px-4 text-gray-600 text-xs">{fix.confidence}</td>
                      <td className="py-3 px-4">
                        {needsOnlineVerification && canVerifyOnline && (
                          <button
                            onClick={() => handleVerifyOnline(idx, fix.field, fix.original)}
                            disabled={verifyingIndex === idx}
                            className="px-3 py-1 text-xs font-semibold bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                          >
                            {verifyingIndex === idx ? '⏳ Verifying...' : '🌐 Verify Online'}
                          </button>
                        )}
                        {needsAiSuggest && (
                          <button
                            onClick={() => handleAiSuggest(idx, fix.field, fix.original)}
                            disabled={aiSuggestIndex === idx}
                            className="ml-2 px-3 py-1 text-xs font-semibold bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                          >
                            {aiSuggestIndex === idx ? '⏳ Suggesting...' : '🤖 AI Suggest'}
                          </button>
                        )}
                        {fix.verified_online && (
                          <span className="text-xs text-green-600 font-semibold">✓ Verified</span>
                        )}
                      </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {fixes.length > 50 && (
                <p className="text-center py-4 text-gray-500 text-sm">Showing first 50 fixes of {fixes.length}</p>
              )}
            </div>
          </div>
        )}

        {/* Data Preview Card */}
        {cleanedData.length > 0 && (
          <div className="bg-white rounded-xl shadow-md border border-gray-100 p-8 mt-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center text-purple-600 font-bold">
                4
              </div>
              <h2 className="text-2xl font-bold text-gray-900">Data Preview</h2>
              <span className="ml-auto text-sm text-gray-600">{cleanedData.length} rows processed</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    {Object.keys(cleanedData[0]).map((col) => (
                      <th key={col} className="text-left py-3 px-4 font-semibold text-gray-700">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {cleanedData.slice(0, 10).map((row, idx) => (
                    <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                      {Object.keys(cleanedData[0]).map((col) => (
                        <td key={col} className="py-3 px-4 text-gray-700">
                          {row[col] !== null && row[col] !== undefined ? String(row[col]).substring(0, 50) : "—"}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {cleanedData.length > 10 && (
                <p className="text-center py-4 text-gray-500 text-sm">Showing first 10 rows of {cleanedData.length}</p>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
