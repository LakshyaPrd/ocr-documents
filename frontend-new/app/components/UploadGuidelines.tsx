/**
 * Upload Guidelines Component
 * Shows best practices for document scanning/uploading
 */

import React from 'react';

interface UploadGuidelinesProps {
  isCollapsed?: boolean;
  onToggle?: () => void;
}

export default function UploadGuidelines({ isCollapsed = false, onToggle }: UploadGuidelinesProps) {
  return (
    <div className="upload-guidelines bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700 rounded-lg p-6 mb-6 border border-blue-200 dark:border-gray-600">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 flex items-center gap-2">
          <span className="text-2xl">📋</span>
          Upload Guidelines - For Best Results
        </h3>
        {onToggle && (
          <button
            onClick={onToggle}
            className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            {isCollapsed ? 'Show' : 'Hide'}
          </button>
        )}
      </div>
      
      {!isCollapsed && (
        <div className="grid md:grid-cols-2 gap-4">
          {/* Lighting & Quality */}
          <div className="space-y-2">
            <h4 className="font-medium text-gray-700 dark:text-gray-200 flex items-center gap-2">
              <span>💡</span> Lighting & Quality
            </h4>
            <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-300">
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">✓</span>
                <span>Ensure document is well-lit (natural light preferred)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-red-500 mt-0.5">✗</span>
                <span>Avoid flash or reflections on the document</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-red-500 mt-0.5">✗</span>
                <span>No shadows or dark spots</span>
              </li>
            </ul>
          </div>

          {/* Positioning */}
          <div className="space-y-2">
            <h4 className="font-medium text-gray-700 dark:text-gray-200 flex items-center gap-2">
              <span>📐</span> Positioning
            </h4>
            <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-300">
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">✓</span>
                <span>Place document on flat surface</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">✓</span>
                <span>Capture all edges clearly</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">✓</span>
                <span>Keep document straight (not tilted)</span>
              </li>
            </ul>
          </div>

          {/* Resolution */}
          <div className="space-y-2">
            <h4 className="font-medium text-gray-700 dark:text-gray-200 flex items-center gap-2">
              <span>🔍</span> Resolution
            </h4>
            <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-300">
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">✓</span>
                <span>Use high resolution (min 300 DPI for scans)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">✓</span>
                <span>Text should be clearly readable</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-red-500 mt-0.5">✗</span>
                <span>Avoid blurry or pixelated images</span>
              </li>
            </ul>
          </div>

          {/* File Format */}
          <div className="space-y-2">
            <h4 className="font-medium text-gray-700 dark:text-gray-200 flex items-center gap-2">
              <span>📄</span> File Format
            </h4>
            <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-300">
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">✓</span>
                <span>Supported: PDF, JPG, PNG, JPEG</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">✓</span>
                <span>Max file size: 10MB recommended</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">✓</span>
                <span>Color or grayscale both work</span>
              </li>
            </ul>
          </div>
        </div>
      )}

      {/* Quick Tips Banner */}
      <div className="mt-4 p-3 bg-blue-100 dark:bg-gray-600 rounded-md">
        <p className="text-sm text-blue-800 dark:text-blue-200 flex items-start gap-2">
          <span className="text-lg">💡</span>
          <span>
            <strong>Pro Tip:</strong> For best accuracy, use a scanner app on your phone or a flatbed scanner. 
            Ensure the entire document is visible with no cut-off edges.
          </span>
        </p>
      </div>
    </div>
  );
}
