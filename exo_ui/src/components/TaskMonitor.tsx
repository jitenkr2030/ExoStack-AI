import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchTasks, fetchTaskDetails } from '../api/tasks';
import { formatDateTime, formatDuration } from '../utils/formatters';
import { Button } from './common/Button';
import { Modal } from './common/Modal';
import { Loader } from './common/Loader';

export const TaskMonitor: React.FC = () => {
  const [selectedTask, setSelectedTask] = useState<string | null>(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);

  const { data: tasks, isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: fetchTasks,
    refetchInterval: 5000,
  });

  const { data: taskDetails, isLoading: detailsLoading } = useQuery({
    queryKey: ['taskDetails', selectedTask],
    queryFn: () => selectedTask ? fetchTaskDetails(selectedTask) : null,
    enabled: !!selectedTask,
  });

  const handleViewDetails = (taskId: string) => {
    setSelectedTask(taskId);
    setIsDetailsModalOpen(true);
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
        Task Monitor
      </h2>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Task ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Model
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Start Time
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Duration
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {tasks?.map((task: any) => (
              <tr key={task.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                  {task.id}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {task.model}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(task.status)}`}>
                    {task.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {formatDateTime(task.startTime)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {formatDuration(task.duration)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleViewDetails(task.id)}
                  >
                    Details
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Task Details Modal */}
      <Modal
        isOpen={isDetailsModalOpen}
        onClose={() => setIsDetailsModalOpen(false)}
        title="Task Details"
      >
        <div className="p-6">
          {detailsLoading ? (
            <Loader />
          ) : taskDetails ? (
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Execution Metrics
                </h3>
                <div className="mt-2 grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Processing Time
                    </p>
                    <p className="text-lg font-medium text-gray-900 dark:text-white">
                      {formatDuration(taskDetails.metrics.processingTime)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Memory Used
                    </p>
                    <p className="text-lg font-medium text-gray-900 dark:text-white">
                      {taskDetails.metrics.memoryUsed} MB
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Input Tokens
                    </p>
                    <p className="text-lg font-medium text-gray-900 dark:text-white">
                      {taskDetails.metrics.inputTokens}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Output Tokens
                    </p>
                    <p className="text-lg font-medium text-gray-900 dark:text-white">
                      {taskDetails.metrics.outputTokens}
                    </p>
                  </div>
                </div>
              </div>

              {taskDetails.error && (
                <div className="mt-4">
                  <h3 className="text-lg font-medium text-red-600">
                    Error Details
                  </h3>
                  <pre className="mt-2 p-4 bg-red-50 text-red-900 rounded-md overflow-x-auto">
                    {taskDetails.error}
                  </pre>
                </div>
              )}

              <div className="mt-6">
                <Button
                  variant="outline"
                  onClick={() => setIsDetailsModalOpen(false)}
                  className="w-full"
                >
                  Close
                </Button>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 dark:text-gray-400">
              No details available
            </p>
          )}
        </div>
      </Modal>
    </div>
  );
};
