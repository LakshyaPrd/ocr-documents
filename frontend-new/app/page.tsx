'use client';

import { useState, useEffect } from 'react';
import DocumentUpload from './components/DocumentUpload';
import ResultsTable from './components/ResultsTable';
import axios from 'axios';

export default function Home() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      const response = await axios.get(`${API_URL}/api/documents`);
      setDocuments(response.data.documents);
    } catch (error) {
      console.error('Error fetching documents:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
    // Poll for updates every 3 seconds
    const interval = setInterval(fetchDocuments, 3000);
    return () => clearInterval(interval);
  }, [refreshKey]);

  const handleUploadSuccess = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12 animate-fade-in">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400 bg-clip-text text-transparent mb-4">
            OCR Document Extraction System
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Upload your documents and extract structured data automatically using advanced OCR technology
          </p>
        </div>

        {/* Upload Section */}
        <div className="mb-12">
          <DocumentUpload onUploadSuccess={handleUploadSuccess} />
        </div>

        {/* Results Section */}
        <div>
          <ResultsTable 
            documents={documents} 
            loading={loading}
            onRefresh={() => setRefreshKey(prev => prev + 1)}
          />
        </div>
      </div>
    </main>
  );
}
