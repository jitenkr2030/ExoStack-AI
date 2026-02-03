import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { SystemMetrics } from './SystemMetrics';
import { NodeList } from './NodeList';
import { ModelManager } from './ModelManager';
import { TaskMonitor } from './TaskMonitor';
import { AlertPanel } from './AlertPanel';
import { fetchSystemStatus, fetchMetrics } from '../api/metrics';
import { Loader } from './common/Loader';
import { ErrorBoundary } from './common/ErrorBoundary';

export const Dashboard: React.FC = () => {
  const { data: systemStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['systemStatus'],
    queryFn: fetchSystemStatus,
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['metrics'],
    queryFn: () => fetchMetrics(),
    refetchInterval: 3000, // Refresh every 3 seconds
  });

  if (statusLoading || metricsLoading) {
    return <Loader />;
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-6">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            ExoStack Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            System Status and Monitoring
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* System Overview */}
          <ErrorBoundary>
            <div className="col-span-full">
              <SystemMetrics metrics={metrics} />
            </div>
          </ErrorBoundary>

          {/* Node Management */}
          <ErrorBoundary>
            <div className="lg:col-span-2">
              <NodeList nodes={systemStatus?.nodes || []} />
            </div>
          </ErrorBoundary>

          {/* Alerts Panel */}
          <ErrorBoundary>
            <div className="lg:col-span-1">
              <AlertPanel />
            </div>
          </ErrorBoundary>

          {/* Task Monitor */}
          <ErrorBoundary>
            <div className="col-span-full">
              <TaskMonitor />
            </div>
          </ErrorBoundary>

          {/* Model Management */}
          <ErrorBoundary>
            <div className="col-span-full">
              <ModelManager />
            </div>
          </ErrorBoundary>
        </div>
      </div>
    </div>
  );
};
