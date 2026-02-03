import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { MetricsCard } from './common/MetricsCard';
import { formatBytes, formatNumber } from '../utils/formatters';

interface SystemMetricsProps {
  metrics: any;
}

export const SystemMetrics: React.FC<SystemMetricsProps> = ({ metrics }) => {
  const cpuData = metrics?.historical?.cpu_usage || [];
  const memoryData = metrics?.historical?.memory_usage || [];
  const gpuData = metrics?.historical?.gpu_usage || [];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
        System Metrics
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* CPU Usage */}
        <MetricsCard
          title="CPU Usage"
          value={`${formatNumber(metrics?.current?.cpu_usage)}%`}
          trend={metrics?.trends?.cpu_usage}
          icon="cpu"
        />

        {/* Memory Usage */}
        <MetricsCard
          title="Memory Usage"
          value={formatBytes(metrics?.current?.memory_used)}
          subValue={`${formatNumber(metrics?.current?.memory_usage)}%`}
          trend={metrics?.trends?.memory_usage}
          icon="memory"
        />

        {/* GPU Usage */}
        <MetricsCard
          title="GPU Usage"
          value={`${formatNumber(metrics?.current?.gpu_usage)}%`}
          subValue={`${metrics?.current?.gpu_count || 0} GPUs`}
          trend={metrics?.trends?.gpu_usage}
          icon="gpu"
        />
      </div>

      {/* Real-time Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CPU & Memory Chart */}
        <div className="h-80">
          <h3 className="text-lg font-medium mb-2 text-gray-900 dark:text-white">
            CPU & Memory Usage
          </h3>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={cpuData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(time) => new Date(time).toLocaleTimeString()}
              />
              <YAxis />
              <Tooltip
                labelFormatter={(label) => new Date(label).toLocaleString()}
              />
              <Line
                type="monotone"
                dataKey="value"
                name="CPU Usage"
                stroke="#3B82F6"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="memory"
                name="Memory Usage"
                stroke="#10B981"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* GPU Usage Chart */}
        <div className="h-80">
          <h3 className="text-lg font-medium mb-2 text-gray-900 dark:text-white">
            GPU Usage
          </h3>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={gpuData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(time) => new Date(time).toLocaleTimeString()}
              />
              <YAxis />
              <Tooltip
                labelFormatter={(label) => new Date(label).toLocaleString()}
              />
              <Line
                type="monotone"
                dataKey="value"
                name="GPU Usage"
                stroke="#8B5CF6"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
