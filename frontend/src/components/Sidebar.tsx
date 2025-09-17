import React from 'react';
import { DocumentIcon, ClockIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { Assignment, AssignmentStatus } from '../types';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorMessage } from './ErrorMessage';

interface SidebarProps {
  assignments: Assignment[];
  selectedAssignment?: Assignment | null;
  onAssignmentSelect?: (assignment: Assignment) => void;
  isLoading?: boolean;
  error?: Error | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  assignments,
  selectedAssignment,
  onAssignmentSelect,
  isLoading = false,
  error = null,
}) => {
  const getStatusIcon = (status: AssignmentStatus) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="w-4 h-4 text-red-500" />;
      case 'processing':
      case 'executing':
        return <LoadingSpinner size="sm" />;
      default:
        return <ClockIcon className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: AssignmentStatus) => {
    switch (status) {
      case 'completed':
        return 'text-green-700 bg-green-100';
      case 'failed':
        return 'text-red-700 bg-red-100';
      case 'processing':
      case 'executing':
        return 'text-blue-700 bg-blue-100';
      case 'planned':
        return 'text-yellow-700 bg-yellow-100';
      default:
        return 'text-gray-700 bg-gray-100';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '';
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
      {/* Sidebar Header */}
      <div className="flex-shrink-0 px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Assignments</h2>
        <p className="text-sm text-gray-500">
          {assignments.length} assignment{assignments.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Assignments List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex justify-center items-center h-full">
            <LoadingSpinner />
          </div>
        ) : error ? (
          <div className="p-6">
            <ErrorMessage message={error.message} />
          </div>
        ) : assignments.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-6">
            <DocumentIcon className="w-12 h-12 text-gray-300 mb-4" />
            <h3 className="text-sm font-medium text-gray-900 mb-2">
              No assignments yet
            </h3>
            <p className="text-xs text-gray-500">
              Upload your first assignment to get started
            </p>
          </div>
        ) : (
          <div className="p-4 space-y-2">
            {assignments.map((assignment) => (
              <div
                key={assignment.id}
                onClick={() => onAssignmentSelect?.(assignment)}
                className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                  selectedAssignment?.id === assignment.id
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-start space-x-3">
                  <DocumentIcon className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-gray-900 truncate">
                      {assignment.title}
                    </h3>
                    <div className="flex items-center space-x-2 mt-1">
                      {getStatusIcon(assignment.status)}
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                          assignment.status
                        )}`}
                      >
                        {assignment.status}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2 mt-2 text-xs text-gray-500">
                      <span>{formatDate(assignment.created_at)}</span>
                      {assignment.file_size && (
                        <>
                          <span>•</span>
                          <span>{formatFileSize(assignment.file_size)}</span>
                        </>
                      )}
                      {assignment.file_type && (
                        <>
                          <span>•</span>
                          <span className="uppercase">{assignment.file_type}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Sidebar Footer */}
      <div className="flex-shrink-0 px-6 py-4 border-t border-gray-200 bg-gray-50">
        <div className="text-xs text-gray-500">
          <div className="flex items-center justify-between">
            <span>System Status</span>
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Online</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
