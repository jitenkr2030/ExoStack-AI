'use client'

import React, { useState, useEffect } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Laptop, 
  Zap, 
  Activity, 
  Battery, 
  Wifi, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  TrendingUp,
  Users,
  Cpu
} from 'lucide-react'

interface Node {
  id: string
  name: string
  status: 'online' | 'offline'
  readinessScore?: number
  isIdle?: boolean
  batteryLevel?: number
  isOnBattery?: boolean
  cpuUsage?: number
  memoryUsage?: number
  gpuAvailable?: boolean
  lastSeen?: string
  tasksCompleted?: number
  tasksFailed?: number
}

interface Task {
  id: string
  title: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  node?: string
  createdAt: string
  duration?: number
  model?: string
}

interface DashboardStats {
  totalNodes: number
  onlineNodes: number
  aiReadyNodes: number
  runningTasks: number
  completedTasks: number
  totalTasks: number
}

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState('overview')
  const [nodes, setNodes] = useState<Node[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [stats, setStats] = useState<DashboardStats>({
    totalNodes: 0,
    onlineNodes: 0,
    aiReadyNodes: 0,
    runningTasks: 0,
    completedTasks: 0,
    totalTasks: 0
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
    const interval = setInterval(fetchDashboardData, 5000) // Refresh every 5 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchDashboardData = async () => {
    try {
      // Fetch nodes from ExoStack API
      const nodesResponse = await fetch('http://localhost:8000/nodes/status')
      const nodesData = await nodesResponse.json()
      
      // Fetch tasks from ExoStack API
      const tasksResponse = await fetch('http://localhost:8000/tasks/status')
      const tasksData = await tasksResponse.json()

      // Transform nodes data
      const transformedNodes = nodesData.map((node: any) => ({
        id: node.id,
        name: node.id,
        status: node.status,
        readinessScore: node.readiness_score,
        isIdle: node.idle_state?.is_idle,
        batteryLevel: node.power_state?.battery_level,
        isOnBattery: node.power_state?.on_battery,
        cpuUsage: node.current_resources?.cpu_usage,
        memoryUsage: node.current_resources?.memory_usage,
        gpuAvailable: node.current_resources?.gpu_available,
        lastSeen: node.last_heartbeat,
        tasksCompleted: node.tasks_completed,
        tasksFailed: node.tasks_failed
      }))

      // Transform tasks data
      const transformedTasks = tasksData.map((task: any) => ({
        id: task.id,
        title: task.id,
        status: task.status,
        node: task.node_id,
        createdAt: task.created_at,
        duration: task.result?.processing_time,
        model: task.model
      }))

      setNodes(transformedNodes)
      setTasks(transformedTasks)

      // Calculate stats
      const onlineNodes = transformedNodes.filter((n: Node) => n.status === 'online').length
      const aiReadyNodes = transformedNodes.filter((n: Node) => n.readinessScore && n.readinessScore >= 60).length
      const runningTasks = transformedTasks.filter((t: Task) => t.status === 'running').length
      const completedTasks = transformedTasks.filter((t: Task) => t.status === 'completed').length

      setStats({
        totalNodes: transformedNodes.length,
        onlineNodes,
        aiReadyNodes,
        runningTasks,
        completedTasks,
        totalTasks: transformedTasks.length
      })

    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'running':
        return 'bg-blue-100 text-blue-800'
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'offline':
      case 'failed':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getReadinessColor = (score?: number) => {
    if (!score) return 'bg-gray-100 text-gray-800'
    if (score >= 80) return 'bg-green-100 text-green-800'
    if (score >= 60) return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  const getBatteryColor = (level?: number) => {
    if (!level) return 'text-gray-500'
    if (level > 60) return 'text-green-500'
    if (level > 20) return 'text-yellow-500'
    return 'text-red-500'
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Compute Dashboard</h1>
          <p className="text-gray-600">Monitor your distributed AI compute network</p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Nodes</CardTitle>
              <Laptop className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalNodes}</div>
              <p className="text-xs text-muted-foreground">
                {stats.onlineNodes} online
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">AI Ready</CardTitle>
              <Zap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.aiReadyNodes}</div>
              <p className="text-xs text-muted-foreground">
                Ready for AI tasks
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Running Tasks</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.runningTasks}</div>
              <p className="text-xs text-muted-foreground">
                Currently executing
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.completedTasks}</div>
              <p className="text-xs text-muted-foreground">
                Total completed
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="nodes">Nodes</TabsTrigger>
            <TabsTrigger value="tasks">Tasks</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Recent Nodes */}
              <Card>
                <CardHeader>
                  <CardTitle>Recent Node Activity</CardTitle>
                  <CardDescription>Your most active AI compute nodes</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {nodes.slice(0, 5).map((node) => (
                      <div key={node.id} className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className={`w-2 h-2 rounded-full ${
                            node.status === 'online' ? 'bg-green-500' : 'bg-red-500'
                          }`} />
                          <div>
                            <p className="text-sm font-medium">{node.name}</p>
                            <p className="text-xs text-gray-500">
                              {node.tasksCompleted || 0} tasks completed
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          {node.readinessScore && (
                            <Badge className={getReadinessColor(node.readinessScore)}>
                              {node.readinessScore}%
                            </Badge>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Recent Tasks */}
              <Card>
                <CardHeader>
                  <CardTitle>Recent AI Tasks</CardTitle>
                  <CardDescription>Latest task executions across your nodes</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {tasks.slice(0, 5).map((task) => (
                      <div key={task.id} className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <Activity className="w-4 h-4 text-blue-500" />
                          <div>
                            <p className="text-sm font-medium">{task.title}</p>
                            <p className="text-xs text-gray-500">
                              {task.model || 'Unknown model'} • {task.node || 'Unknown node'}
                            </p>
                          </div>
                        </div>
                        <Badge className={getStatusColor(task.status)}>
                          {task.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="nodes" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Your AI Compute Nodes</CardTitle>
                <CardDescription>Monitor and manage your laptop nodes</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {nodes.map((node) => (
                    <div key={node.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <Laptop className="w-5 h-5 text-blue-500" />
                          <div>
                            <h3 className="font-medium">{node.name}</h3>
                            <p className="text-sm text-gray-500">
                              Last seen: {node.lastSeen ? new Date(node.lastSeen).toLocaleString() : 'Never'}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge className={getStatusColor(node.status)}>
                            {node.status}
                          </Badge>
                          {node.readinessScore && (
                            <Badge className={getReadinessColor(node.readinessScore)}>
                              AI: {node.readinessScore}%
                            </Badge>
                          )}
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div className="flex items-center space-x-2">
                          <Zap className="w-4 h-4 text-yellow-500" />
                          <span>Idle: {node.isIdle ? 'Yes' : 'No'}</span>
                        </div>
                        
                        {node.batteryLevel !== undefined && (
                          <div className="flex items-center space-x-2">
                            <Battery className={`w-4 h-4 ${getBatteryColor(node.batteryLevel)}`} />
                            <span>{node.isOnBattery ? `Battery ${node.batteryLevel}%` : 'Plugged In'}</span>
                          </div>
                        )}
                        
                        {node.cpuUsage !== undefined && (
                          <div className="flex items-center space-x-2">
                            <Cpu className="w-4 h-4 text-purple-500" />
                            <span>CPU: {node.cpuUsage.toFixed(1)}%</span>
                          </div>
                        )}
                        
                        {node.gpuAvailable !== undefined && (
                          <div className="flex items-center space-x-2">
                            <Activity className="w-4 h-4 text-green-500" />
                            <span>GPU: {node.gpuAvailable ? 'Available' : 'N/A'}</span>
                          </div>
                        )}
                      </div>

                      <div className="mt-3 pt-3 border-t text-sm text-gray-600">
                        Tasks: {node.tasksCompleted || 0} completed, {node.tasksFailed || 0} failed
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="tasks" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>AI Task History</CardTitle>
                <CardDescription>Complete history of AI tasks across your network</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {tasks.map((task) => (
                    <div key={task.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <Activity className="w-5 h-5 text-blue-500" />
                          <div>
                            <h3 className="font-medium">{task.title}</h3>
                            <p className="text-sm text-gray-500">
                              Created: {new Date(task.createdAt).toLocaleString()}
                            </p>
                            {task.node && (
                              <p className="text-sm text-gray-500">Node: {task.node}</p>
                            )}
                            {task.model && (
                              <p className="text-sm text-gray-500">Model: {task.model}</p>
                            )}
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge className={getStatusColor(task.status)}>
                            {task.status}
                          </Badge>
                          {task.duration && (
                            <p className="text-sm text-gray-500 mt-1">
                              {task.duration.toFixed(2)}s
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  )
}