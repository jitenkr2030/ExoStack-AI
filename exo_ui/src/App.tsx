import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, Server, Cpu, AlertCircle, CheckCircle, Battery, Wifi, WifiOff, Zap, Laptop, Power } from 'lucide-react';

interface Node {
  id: string;
  status: 'online' | 'offline';
  last_heartbeat: string;
  tasks_completed?: number;
  tasks_failed?: number;
  current_load?: number;
  active_tasks?: number;
  health_score?: number;
  host?: string;
  port?: number;
  // AI compute readiness
  ready_for_ai?: boolean;
  readiness_score?: number;
  idle_state?: {
    is_idle: boolean;
    idle_duration: number;
    user_active: boolean;
  };
  power_state?: {
    on_battery: boolean;
    battery_level: number;
    power_plugged: boolean;
  };
  current_resources?: {
    cpu_usage: number;
    memory_usage: number;
    gpu_available: boolean;
  };
  laptop_optimized?: boolean;
}

interface Task {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'rejected';
  node_id?: string;
  created_at: string;
  model?: string;
  result?: {
    output?: string;
    processing_time?: number;
    tokens_generated?: number;
    error?: string;
  };
}

interface SystemStats {
  nodes: {
    total: number;
    online: number;
    offline: number;
    ai_ready: number;
  };
  tasks: {
    pending: number;
    running: number;
    completed: number;
    failed: number;
    total: number;
  };
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setError(null);
      const [nodesResponse, tasksResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/nodes/status`),
        axios.get(`${API_BASE_URL}/tasks/status`)
      ]);
      
      setNodes(nodesResponse.data);
      setTasks(tasksResponse.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
      case 'completed':
        return 'text-green-500';
      case 'running':
        return 'text-blue-500';
      case 'pending':
        return 'text-yellow-500';
      case 'offline':
      case 'failed':
      case 'rejected':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
      case 'completed':
        return <CheckCircle className="w-4 h-4" />;
      case 'running':
        return <Activity className="w-4 h-4" />;
      case 'offline':
      case 'failed':
      case 'rejected':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Server className="w-4 h-4" />;
    }
  };

  const getReadinessColor = (score?: number) => {
    if (!score) return 'bg-gray-100 text-gray-800';
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getBatteryColor = (level?: number) => {
    if (!level) return 'text-gray-500';
    if (level > 60) return 'text-green-500';
    if (level > 20) return 'text-yellow-500';
    return 'text-red-500';
  };

  const formatIdleDuration = (seconds?: number) => {
    if (!seconds) return 'Not idle';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const aiReadyNodes = nodes.filter(n => n.ready_for_ai).length;
  const laptopNodes = nodes.filter(n => n.laptop_optimized).length;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="flex items-center space-x-2">
          <Activity className="w-6 h-6 animate-spin" />
          <span>Loading ExoStack AI Dashboard...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-3">
              <Laptop className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">ExoStack AI</h1>
                <p className="text-sm text-gray-500">Turning Idle Laptops into AI Powerhouses</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <span className="text-sm text-gray-500">AI Ready Nodes</span>
                <p className="text-lg font-semibold text-green-600">{aiReadyNodes}/{nodes.length}</p>
              </div>
              <span className="text-sm text-gray-500">
                Last updated: {new Date().toLocaleTimeString()}
              </span>
              <button
                onClick={fetchData}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-400 mr-2" />
              <span className="text-red-800">Error: {error}</span>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* AI Laptop Nodes Section */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                <Laptop className="w-5 h-5 mr-2" />
                AI Laptop Nodes ({laptopNodes})
              </h2>
            </div>
            <div className="p-6">
              {nodes.length === 0 ? (
                <p className="text-gray-500 text-center py-4">No laptop nodes registered</p>
              ) : (
                <div className="space-y-4">
                  {nodes.map((node) => (
                    <div key={node.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <span className={getStatusColor(node.status)}>
                            {getStatusIcon(node.status)}
                          </span>
                          <div>
                            <h3 className="font-medium text-gray-900 flex items-center">
                              {node.id}
                              {node.laptop_optimized && (
                                <Laptop className="w-4 h-4 ml-2 text-blue-500" />
                              )}
                            </h3>
                            <p className="text-sm text-gray-500">
                              Last heartbeat: {new Date(node.last_heartbeat).toLocaleString()}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            node.status === 'online' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {node.status}
                          </span>
                          {node.readiness_score !== undefined && (
                            <div className="mt-1">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getReadinessColor(node.readiness_score)}`}>
                                AI: {node.readiness_score}%
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* AI Compute Readiness Details */}
                      {node.ready_for_ai !== undefined && (
                        <div className="grid grid-cols-2 gap-4 mt-3 text-sm">
                          <div className="flex items-center space-x-2">
                            <Zap className="w-4 h-4 text-yellow-500" />
                            <span className="text-gray-600">AI Ready:</span>
                            <span className={node.ready_for_ai ? 'text-green-600' : 'text-red-600'}>
                              {node.ready_for_ai ? 'Yes' : 'No'}
                            </span>
                          </div>
                          
                          {node.idle_state && (
                            <div className="flex items-center space-x-2">
                              <Activity className="w-4 h-4 text-blue-500" />
                              <span className="text-gray-600">Idle:</span>
                              <span className={node.idle_state.is_idle ? 'text-green-600' : 'text-gray-600'}>
                                {node.idle_state.is_idle ? formatIdleDuration(node.idle_state.idle_duration) : 'Active'}
                              </span>
                            </div>
                          )}
                          
                          {node.power_state && (
                            <div className="flex items-center space-x-2">
                              <Battery className={`w-4 h-4 ${getBatteryColor(node.power_state.battery_level)}`} />
                              <span className="text-gray-600">Power:</span>
                              <span className={node.power_state.on_battery ? 'text-yellow-600' : 'text-green-600'}>
                                {node.power_state.on_battery ? `Battery ${node.power_state.battery_level}%` : 'Plugged In'}
                              </span>
                            </div>
                          )}
                          
                          {node.current_resources && (
                            <div className="flex items-center space-x-2">
                              <Cpu className="w-4 h-4 text-purple-500" />
                              <span className="text-gray-600">GPU:</span>
                              <span className={node.current_resources.gpu_available ? 'text-green-600' : 'text-gray-600'}>
                                {node.current_resources.gpu_available ? 'Available' : 'N/A'}
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                      
                      <div className="mt-3 text-sm text-gray-500">
                        Tasks: {node.tasks_completed || 0} completed, {node.tasks_failed || 0} failed
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* AI Tasks Section */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                <Activity className="w-5 h-5 mr-2" />
                AI Compute Tasks ({tasks.length})
              </h2>
            </div>
            <div className="p-6">
              {tasks.length === 0 ? (
                <p className="text-gray-500 text-center py-4">No AI tasks found</p>
              ) : (
                <div className="space-y-4">
                  {tasks.slice(0, 10).map((task) => (
                    <div key={task.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <span className={getStatusColor(task.status)}>
                            {getStatusIcon(task.status)}
                          </span>
                          <div>
                            <h3 className="font-medium text-gray-900">{task.id}</h3>
                            <p className="text-sm text-gray-500">
                              Created: {new Date(task.created_at).toLocaleString()}
                            </p>
                            {task.node_id && (
                              <p className="text-sm text-gray-500">Node: {task.node_id}</p>
                            )}
                            {task.model && (
                              <p className="text-sm text-gray-500">Model: {task.model}</p>
                            )}
                          </div>
                        </div>
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          task.status === 'completed' ? 'bg-green-100 text-green-800' :
                          task.status === 'running' ? 'bg-blue-100 text-blue-800' :
                          task.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          task.status === 'rejected' ? 'bg-red-200 text-red-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {task.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* AI Compute Summary Stats */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <Laptop className="w-8 h-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Laptops</p>
                <p className="text-2xl font-semibold text-gray-900">{laptopNodes}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <Zap className="w-8 h-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">AI Ready</p>
                <p className="text-2xl font-semibold text-gray-900">{aiReadyNodes}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <CheckCircle className="w-8 h-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Online Nodes</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {nodes.filter(n => n.status === 'online').length}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <Activity className="w-8 h-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Running AI Tasks</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {tasks.filter(t => t.status === 'running').length}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <CheckCircle className="w-8 h-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Completed AI Tasks</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {tasks.filter(t => t.status === 'completed').length}
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
