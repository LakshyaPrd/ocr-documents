'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

interface DocumentType {
  key: string;
  name: string;
  fields_count: number;
}

interface DocumentUploadProps {
  onUploadSuccess: () => void;
}

export default function DocumentUpload({ onUploadSuccess }: DocumentUploadProps) {
  const [documentTypes, setDocumentTypes] = useState<DocumentType[]>([]);
  const [selectedType, setSelectedType] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [loadingTypes, setLoadingTypes] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDocumentTypes();
  }, []);

  const fetchDocumentTypes = async () => {
    try {
      setLoadingTypes(true);
      setError('');
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      const response = await axios.get<DocumentType[]>(`${API_URL}/api/document-types`);
      console.log('Document types loaded:', response.data);
      setDocumentTypes(response.data);
    } catch (error: any) {
      console.error('Error fetching document types:', error);
      setError('Failed to load document types. Make sure backend is running on port 8000.');
    } finally {
      setLoadingTypes(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files && files[0]) {
      setSelectedFile(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      setSelectedFile(files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !selectedType) {
      setUploadStatus('Please select both a document type and file');
      return;
    }

    setUploading(true);
    setUploadStatus('Uploading...');

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('document_type', selectedType);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      const response = await axios.post(`${API_URL}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadStatus('✅ Upload successful! Processing started...');
      setSelectedFile(null);
      setSelectedType('');
      onUploadSuccess();

      // Clear status after 3 seconds
      setTimeout(() => setUploadStatus(''), 3000);
    } catch (error: any) {
      setUploadStatus(`❌ Upload failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-6">
        Upload Document
      </h2>

      {error && (
        <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-red-600 dark:text-red-400 text-sm">
            {error}
          </p>
          <button onClick={fetchDocumentTypes} className="mt-2 text-sm text-red-700 dark:text-red-300 underline">
            Try Again
          </button>
        </div>
      )}

      {/* Document Type Selector */}
      <div className="mb-6">
        <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
          Select Document Type {loadingTypes && <span className="text-xs text-gray-500">(Loading...)</span>}
        </label>
        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          className="input-field"
          disabled={loadingTypes}
        >
          <option value="">-- Choose Document Type --</option>
          {documentTypes.map((type) => (
            <option key={type.key} value={type.key}>
              {type.name} ({type.fields_count} fields)
            </option>
          ))}
        </select>
        {documentTypes.length === 0 && !loadingTypes && !error && (
          <p className="text-xs text-gray-500 mt-1">No document types available</p>
        )}
      </div>

      {/* File Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300
          ${isDragging 
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
            : 'border-gray-300 dark:border-gray-600 hover:border-blue-400'
          }
        `}
      >
        <div className="space-y-4">
          <div className="text-6xl">📄</div>
          <div>
            <p className="text-lg font-semibold text-gray-700 dark:text-gray-300">
              {selectedFile ? selectedFile.name : 'Drag & drop your file here'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
              or click to browse
            </p>
          </div>
          <input
            type="file"
            onChange={handleFileSelect}
            accept=".pdf,.png,.jpg,.jpeg"
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="inline-block btn-secondary cursor-pointer"
          >
            Browse Files
          </label>
          <p className="text-xs text-gray-400">
            Supported formats: PDF, PNG, JPG, JPEG (Max 10MB)
          </p>
        </div>
      </div>

      {/* Upload Button */}
      <div className="mt-6 flex items-center justify-between">
        <button
          onClick={handleUpload}
          disabled={!selectedFile || !selectedType || uploading}
          className="btn-primary"
        >
          {uploading ? (
            <>
              <span className="inline-block animate-spin mr-2">⚙️</span>
              Processing...
            </>
          ) : (
            <>
              <span className="mr-2">🚀</span>
              Upload & Extract
            </>
          )}
        </button>

        {uploadStatus && (
          <p className={`text-sm font-medium ${
            uploadStatus.startsWith('✅') 
              ? 'text-green-600 dark:text-green-400' 
              : uploadStatus.startsWith('❌')
              ? 'text-red-600 dark:text-red-400'
              : 'text-gray-600 dark:text-gray-400'
          }`}>
            {uploadStatus}
          </p>
        )}
      </div>
    </div>
  );
}
