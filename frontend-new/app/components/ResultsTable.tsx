'use client';

import { useState, Fragment } from 'react';
import axios from 'axios';
import { API_URL } from '../config';

interface ExtractedField {
  field_name: string;
  field_value: string | null;
  confidence: number;
  page_number: number;
}

interface Document {
  id: number;
  document_type: string;
  original_filename: string;
  file_size: number;
  upload_date: string;
  status: string;
  ocr_confidence: number;
  error_message: string | null;
  extracted_fields: ExtractedField[];
}

interface ResultsTableProps {
  documents: Document[];
  loading: boolean;
  onRefresh: () => void;
}

export default function ResultsTable({ documents, loading, onRefresh }: ResultsTableProps) {
  const [expandedDoc, setExpandedDoc] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    
    setDeletingId(id);
    try {
      await axios.delete(`${API_URL}/api/documents/${id}`);
      onRefresh();
    } catch (error) {
      console.error('Error deleting document:', error);
      alert('Failed to delete document');
    } finally {
      setDeletingId(null);
    }
  };

  const exportToCSV = () => {
    if (documents.length === 0) return;

    const headers = ['Document ID', 'Document Type', 'Filename', 'Fields Extracted', 'Upload Date'];
    const rows = documents.map(doc => [
      doc.id,
      doc.document_type.replace('_', ' '),
      doc.original_filename,
      doc.extracted_fields.length,
      new Date(doc.upload_date).toLocaleString()
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ocr-documents-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          Extracted Documents ({documents.length})
        </h2>
        <div className="flex gap-3">
          <button
            onClick={onRefresh}
            className="px-5 py-2.5 bg-gradient-to-r from-gray-100 to-gray-200 hover:from-gray-200 hover:to-gray-300 text-gray-700 font-semibold rounded-xl transition-all duration-300 shadow-sm hover:shadow-md disabled:opacity-50"
            disabled={loading}
          >
            {loading ? '⟳ Refreshing...' : '🔄 Refresh'}
          </button>
          <button
            onClick={exportToCSV}
            className="px-5 py-2.5 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-semibold rounded-xl transition-all duration-300 shadow-md hover:shadow-lg disabled:opacity-50"
            disabled={documents.length === 0}
          >
            📥 Export CSV
          </button>
        </div>
      </div>

      {loading && documents.length === 0 ? (
        <div className="text-center py-16">
          <div className="inline-block animate-spin text-6xl mb-4">⚙️</div>
          <p className="text-gray-600 text-lg">Loading documents...</p>
        </div>
      ) : documents.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-7xl mb-4">📭</div>
          <p className="text-gray-700 text-xl mb-2">No documents uploaded yet</p>
          <p className="text-gray-500">Upload a document to get started</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-gray-200">
          <table className="w-full">
            <thead className="bg-gradient-to-r from-gray-50 to-gray-100">
              <tr>
                <th className="text-left py-4 px-6 font-bold text-gray-700">Document Type</th>
                <th className="text-left py-4 px-6 font-bold text-gray-700">Filename</th>
                <th className="text-left py-4 px-6 font-bold text-gray-700">Fields Extracted</th>
                <th className="text-left py-4 px-6 font-bold text-gray-700">Upload Date</th>
                <th className="text-left py-4 px-6 font-bold text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white">
              {documents.map((doc) => (
                <Fragment key={doc.id}>
                  <tr
                    className="border-b border-gray-100 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 transition-all duration-200"
                  >
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">
                          {doc.document_type === 'PASSPORT' ? '🛂' :
                           doc.document_type === 'LABOR_CARD' ? '💼' :
                           doc.document_type === 'RESIDENCE_VISA' ? '🏠' :
                           doc.document_type === 'EMIRATES_ID' ? '🆔' : '📄'}
                        </span>
                        <span className="font-semibold text-gray-800">
                          {doc.document_type.replace('_', ' ')}
                        </span>
                      </div>
                    </td>
                    <td className="py-4 px-6 text-gray-700">
                      {doc.original_filename}
                    </td>
                    <td className="py-4 px-6">
                      {doc.status === 'processing' || doc.status === 'pending' ? (
                        <span className="inline-flex items-center gap-2 px-3 py-1 bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-700 font-semibold rounded-full animate-pulse">
                          <span className="inline-block animate-spin">⚙️</span>
                          Processing...
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-3 py-1 bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 font-semibold rounded-full">
                          {doc.extracted_fields.length} fields
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-6 text-gray-600">
                      {new Date(doc.upload_date).toLocaleDateString()}
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex gap-3">
                        <button
                          onClick={() => setExpandedDoc(expandedDoc === doc.id ? null : doc.id)}
                          className="text-blue-600 hover:text-blue-700 font-semibold transition-colors"
                        >
                          {expandedDoc === doc.id ? '▲ Hide' : '▼ View'}
                        </button>
                        <button
                          onClick={() => handleDelete(doc.id)}
                          disabled={deletingId === doc.id}
                          className="text-red-600 hover:text-red-700 font-semibold transition-colors disabled:opacity-50"
                        >
                          {deletingId === doc.id ? '⏳' : '🗑️'}
                        </button>
                      </div>
                    </td>
                  </tr>

                  {/* Expanded Row - Clean Field Display */}
                  {expandedDoc === doc.id && (
                    <tr>
                      <td colSpan={5} className="py-6 px-6 bg-gradient-to-br from-gray-50 to-blue-50">
                        <div>
                          <h3 className="font-bold text-xl text-gray-800 mb-6 flex items-center gap-2">
                            <span>📋</span>
                            Extracted Information
                          </h3>
                          
                          {doc.status === 'processing' || doc.status === 'pending' ? (
                            <div className="text-center py-12">
                              <div className="inline-block text-6xl mb-4 animate-spin">⚙️</div>
                              <p className="text-gray-700 text-lg font-semibold">Processing document...</p>
                              <p className="text-gray-500 mt-2">Extracting fields using AI-powered OCR</p>
                            </div>
                          ) : doc.extracted_fields.length === 0 ? (
                            <p className="text-gray-500 italic py-4">
                              No fields extracted.
                            </p>
                          ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                              {doc.extracted_fields.map((field, idx) => (
                                <div
                                  key={idx}
                                  className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
                                >
                                  <span className="text-xs font-bold text-gray-500 uppercase tracking-wider block mb-2">
                                    {field.field_name.replace(/_/g, ' ')}
                                  </span>
                                  <p className="text-gray-900 font-semibold text-lg">
                                    {field.field_value || <span className="text-gray-400 italic font-normal">Not found</span>}
                                  </p>
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Export Button */}
                          <div className="mt-6 pt-6 border-t border-gray-200">
                            <button
                              className="px-5 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold rounded-xl transition-all duration-300 shadow-md hover:shadow-lg"
                              onClick={() => {
                                const data = doc.extracted_fields.map(f => ({
                                  field: f.field_name,
                                  value: f.field_value
                                }));
                                const csv = [
                                  'Field,Value',
                                  ...data.map(d => `"${d.field}","${d.value}"`)
                                ].join('\n');
                                const blob = new Blob([csv], { type: 'text/csv' });
                                const url = window.URL.createObjectURL(blob);
                                const a = document.createElement('a');
                                a.href = url;
                                a.download = `${doc.original_filename.split('.')[0]}-data.csv`;
                                a.click();
                              }}
                            >
                              📥 Export This Document
                            </button>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
