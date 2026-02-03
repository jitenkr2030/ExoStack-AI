import React from 'react';
import { Icon } from 'lucide-react';

interface MetricsCardProps {
  title: string;
  value: string;
  subValue?: string;
  trend?: number;
  icon?: string;
}

export const MetricsCard: React.FC<MetricsCardProps> = ({
  title,
  value,
  subValue,
  trend,
  icon
}) => {
  const getTrendColor = (trend: number) => {
    if (trend > 0) return 'text-red-500';
    if (trend < 0) return 'text-green-500';
    return 'text-gray-500';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          {title}
        </h3>
        {icon && (
          <Icon
            name={icon}
            className="h-6 w-6 text-gray-400"
          />
        )}
      </div>
      <div className="mt-2">
        <div className="text-3xl font-bold text-gray-900 dark:text-white">
          {value}
        </div>
        {subValue && (
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {subValue}
          </div>
        )}
        {trend !== undefined && (
          <div className={`mt-2 flex items-center ${getTrendColor(trend)}`}>
            <Icon
              name={trend > 0 ? 'trending-up' : 'trending-down'}
              className="h-4 w-4 mr-1"
            />
            <span className="text-sm">
              {Math.abs(trend)}% from last hour
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
