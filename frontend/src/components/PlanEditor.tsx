import React, { useState } from 'react';
import { useQuery } from 'react-query';
import {
  PlayIcon,
  PauseIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ChevronDownIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline';
import { api } from '../lib/api';
import { Assignment, Plan, Task, TaskStatus, PlanStatus } from '../types';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorMessage } from './ErrorMessage';

interface PlanEditorProps {
  assignment?: Assignment | null;
  plans: Plan[];
  selectedPlan?: Plan | null;
  onPlanSelect?: (plan: Plan) => void;
  onExecutePlan?: (planId: string) => void;
  isLoading?: boolean;
  isExecuting?: boolean;
}

export const PlanEditor: React.FC<PlanEditorProps> = ({
  assignment,
  plans,
  selectedPlan,
  onPlanSelect,
  onExecutePlan,
  isLoading = false,
  isExecuting = false,
}) => {
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());

  // Fetch plan status if a plan is selected
  const { data: planStatus } = useQuery(
    ['planStatus', selectedPlan?.id],
    () => api.getPlanStatus(selectedPlan!.id),
    {
      enabled: !!selectedPlan?.id,
      refetchInterval: 2000, // Poll every 2 seconds for real-time updates
    }
  );

  const toggleTaskExpansion = (taskId: string) => {
    const newExpanded = new Set(expandedTasks);
    if (newExpanded.has(taskId)) {
      newExpanded.delete(taskId);
    } else {
      newExpanded.add(taskId);
    }
    setExpandedTasks(newExpanded);
  };

  const getStatusIcon = (status: TaskStatus | PlanStatus) => {
    switch (status) {
      case 'success':
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      case 'running':
      case 'executing':
        return <LoadingSpinner size="sm" />;
      case 'pending':
      case 'created':
        return <ClockIcon className="w-5 h-5 text-gray-400" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: TaskStatus | PlanStatus) => {
    switch (status) {
      case 'success':
      case 'completed':
        return 'text-green-700 bg-green-100';
      case 'failed':
        return 'text-red-700 bg-red-100';
      case 'running':
      case 'executing':
        return 'text-blue-700 bg-blue-100';
      case 'pending':
      case 'created':
        return 'text-gray-700 bg-gray-100';
      default:
        return 'text-gray-700 bg-gray-100';
    }
  };

  const formatDuration = (minutes?: number) => {
    if (!minutes) return 'N/A';
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
  };

  const TaskItem: React.FC<{ task: Task; level: number }> = ({ task, level }) => {
    const isExpanded = expandedTasks.has(task.id);
    const hasChildren = task.dependencies && task.dependencies.length > 0;

    return (
      <div className={`ml-${level * 4}`}>
        <div
          className={`flex items-center space-x-3 p-3 rounded-lg border ${
            selectedPlan?.id === task.id ? 'border-primary-500 bg-primary-50' : 'border-gray-200'
          }`}
        >
          {/* Expand/Collapse Button */}
          {hasChildren && (
            <button
              onClick={() => toggleTaskExpansion(task.id)}
              className="text-gray-400 hover:text-gray-600"
            >
              {isExpanded ? (
                <ChevronDownIcon className="w-4 h-4" />
              ) : (
                <ChevronRightIcon className="w-4 h-4" />
              )}
            </button>
          )}

          {/* Status Icon */}
          {getStatusIcon(task.status)}

          {/* Task Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2">
              <h4 className="text-sm font-medium text-gray-900 truncate">
                {task.description}
              </h4>
              <span
                className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
                  task.status
                )}`}
              >
                {task.status}
              </span>
            </div>
            <div className="flex items-center space-x-4 mt-1">
              <span className="text-xs text-gray-500">
                Type: {task.task_type}
              </span>
              <span className="text-xs text-gray-500">
                Duration: {formatDuration(task.estimated_duration)}
              </span>
              {task.tool_requirements.length > 0 && (
                <span className="text-xs text-gray-500">
                  Tools: {task.tool_requirements.join(', ')}
                </span>
              )}
            </div>
          </div>

          {/* Task Actions */}
          <div className="flex items-center space-x-2">
            {task.status === 'failed' && (
              <button
                onClick={() => {
                  // Retry task logic would go here
                  console.log('Retry task:', task.id);
                }}
                className="text-xs text-primary-600 hover:text-primary-800"
              >
                Retry
              </button>
            )}
          </div>
        </div>

        {/* Task Details */}
        {isExpanded && (
          <div className="ml-8 mt-2 space-y-2">
            {task.parameters && Object.keys(task.parameters).length > 0 && (
              <div className="bg-gray-50 p-3 rounded-lg">
                <h5 className="text-xs font-medium text-gray-700 mb-2">Parameters</h5>
                <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                  {JSON.stringify(task.parameters, null, 2)}
                </pre>
              </div>
            )}

            {task.result && (
              <div className="bg-gray-50 p-3 rounded-lg">
                <h5 className="text-xs font-medium text-gray-700 mb-2">Result</h5>
                <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                  {JSON.stringify(task.result, null, 2)}
                </pre>
              </div>
            )}

            {task.error_message && (
              <div className="bg-red-50 p-3 rounded-lg">
                <h5 className="text-xs font-medium text-red-700 mb-2">Error</h5>
                <p className="text-xs text-red-600">{task.error_message}</p>
              </div>
            )}

            {/* Dependencies */}
            {task.dependencies && task.dependencies.length > 0 && (
              <div className="bg-blue-50 p-3 rounded-lg">
                <h5 className="text-xs font-medium text-blue-700 mb-2">Dependencies</h5>
                <div className="space-y-1">
                  {task.dependencies.map((dep, index) => (
                    <div key={index} className="text-xs text-blue-600">
                      • {dep.task_id} ({dep.dependency_type})
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Render child tasks */}
        {isExpanded && hasChildren && (
          <div className="mt-2 space-y-2">
            {task.dependencies?.map((dep, index) => {
              // In a real implementation, you'd find the actual task object
              // For now, we'll just show the dependency ID
              return (
                <div key={index} className="ml-4 p-2 bg-gray-100 rounded text-xs text-gray-600">
                  Dependency: {dep.task_id}
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex-shrink-0 px-6 py-4 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Execution Plans</h2>
            {assignment && (
              <p className="text-sm text-gray-500">
                Plans for: {assignment.title}
              </p>
            )}
          </div>
          {selectedPlan && selectedPlan.status === 'created' && (
            <button
              onClick={() => onExecutePlan?.(selectedPlan.id)}
              disabled={isExecuting}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isExecuting ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Executing...
                </>
              ) : (
                <>
                  <PlayIcon className="w-4 h-4 mr-2" />
                  Execute Plan
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex justify-center items-center h-full">
            <LoadingSpinner />
          </div>
        ) : plans.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-6">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
              <ClockIcon className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No Plans Available
            </h3>
            <p className="text-gray-500 max-w-md">
              {assignment
                ? `No execution plans have been generated for "${assignment.title}" yet. Use the chat to generate a plan.`
                : 'Select an assignment to view its execution plans.'}
            </p>
          </div>
        ) : (
          <div className="p-6 space-y-6">
            {/* Plans List */}
            <div className="space-y-4">
              {plans.map((plan) => (
                <div
                  key={plan.id}
                  className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                    selectedPlan?.id === plan.id
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => onPlanSelect?.(plan)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(plan.status)}
                      <div>
                        <h3 className="text-sm font-medium text-gray-900">
                          {plan.name}
                        </h3>
                        <p className="text-xs text-gray-500">
                          {plan.tasks.length} tasks • {formatDuration(plan.total_estimated_duration)} estimated
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
                          plan.status
                        )}`}
                      >
                        {plan.status}
                      </span>
                      {planStatus && plan.id === selectedPlan?.id && (
                        <span className="text-xs text-gray-500">
                          {planStatus.completed_tasks}/{planStatus.total_tasks} completed
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Selected Plan Details */}
            {selectedPlan && (
              <div className="border-t pt-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900">
                    {selectedPlan.name}
                  </h3>
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(selectedPlan.status)}
                    <span
                      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
                        selectedPlan.status
                      )}`}
                    >
                      {selectedPlan.status}
                    </span>
                  </div>
                </div>

                {selectedPlan.description && (
                  <p className="text-sm text-gray-600 mb-4">
                    {selectedPlan.description}
                  </p>
                )}

                {/* Tasks */}
                <div className="space-y-3">
                  <h4 className="text-sm font-medium text-gray-900">Tasks</h4>
                  {selectedPlan.tasks.map((task) => (
                    <TaskItem key={task.id} task={task} level={0} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
