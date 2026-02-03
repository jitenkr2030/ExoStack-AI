import { PrismaClient } from '@prisma/client'
import bcrypt from 'bcryptjs'

const prisma = new PrismaClient()

async function main() {
  console.log('Start seeding...')

  // Create demo user
  const hashedPassword = await bcrypt.hash('password123', 12)
  
  const demoUser = await prisma.user.create({
    data: {
      email: 'demo@exostack.ai',
      username: 'demo',
      password: hashedPassword,
      firstName: 'Demo',
      lastName: 'User',
      emailVerified: true,
      isActive: true,
      isPremium: false,
      maxNodes: 5,
      maxTasks: 100,
      loginCount: 1,
      lastLogin: new Date(),
    },
  })

  // Create user profile
  await prisma.userProfile.create({
    data: {
      userId: demoUser.id,
      bio: 'Demo user for ExoStack AI platform',
      company: 'ExoStack AI',
      location: 'San Francisco, CA',
      website: 'https://exostack.ai',
      github: 'exostack',
      twitter: 'exostack_ai',
      theme: 'light',
      emailDigest: true,
      taskNotifications: true,
      nodeAlerts: true,
    },
  })

  // Create demo nodes
  await prisma.node.createMany({
    data: [
      {
        userId: demoUser.id,
        nodeId: 'demo-laptop-1',
        name: 'Demo Laptop 1',
        description: 'Primary development laptop',
        cpuCores: 8,
        memoryGb: 16.0,
        gpuAvailable: true,
        gpuType: 'NVIDIA RTX 3080',
        osType: 'macOS',
        osVersion: '13.6',
        status: 'online',
        lastSeen: new Date(),
        maxConcurrentTasks: 3,
        enabledTasks: ['text_generation', 'image_generation'],
      },
      {
        userId: demoUser.id,
        nodeId: 'demo-laptop-2',
        name: 'Demo Laptop 2',
        description: 'Secondary work laptop',
        cpuCores: 6,
        memoryGb: 32.0,
        gpuAvailable: false,
        osType: 'Windows',
        osVersion: '11',
        status: 'offline',
        lastSeen: new Date(Date.now() - 3600000), // 1 hour ago
        maxConcurrentTasks: 2,
        enabledTasks: ['text_generation'],
      },
    ],
  })

  // Create demo tasks
  const nodes = await prisma.node.findMany({
    where: { userId: demoUser.id },
  })

  if (nodes.length > 0) {
    await prisma.task.createMany({
      data: [
        {
          nodeId: nodes[0].id,
          taskId: 'demo-task-1',
          title: 'Text Generation Demo',
          taskType: 'text_generation',
          model: 'gpt2',
          status: 'completed',
          config: { max_tokens: 100, temperature: 0.7 },
          input: { prompt: 'Once upon a time' },
          output: { text: 'Once upon a time, in a land far away...' },
          startedAt: new Date(Date.now() - 300000), // 5 minutes ago
          completedAt: new Date(Date.now() - 240000), // 4 minutes ago
          duration: 60,
          tokensUsed: 150,
          cost: 0.002,
        },
        {
          nodeId: nodes[0].id,
          taskId: 'demo-task-2',
          title: 'Image Generation Demo',
          taskType: 'image_generation',
          model: 'stable-diffusion',
          status: 'running',
          config: { width: 512, height: 512, steps: 20 },
          input: { prompt: 'A beautiful sunset over mountains' },
          startedAt: new Date(Date.now() - 120000), // 2 minutes ago
        },
        {
          nodeId: nodes[1].id,
          taskId: 'demo-task-3',
          title: 'Code Generation Demo',
          taskType: 'code_generation',
          model: 'codex',
          status: 'failed',
          config: { language: 'python', max_tokens: 200 },
          input: { prompt: 'Write a hello world function' },
          startedAt: new Date(Date.now() - 7200000), // 2 hours ago
          completedAt: new Date(Date.now() - 7000000), // 1 hour 57 minutes ago
          duration: 120,
          cost: 0.005,
        },
      ],
    })
  }

  console.log('Seeding finished.')
}

main()
  .then(async () => {
    await prisma.$disconnect()
  })
  .catch(async (e) => {
    console.error(e)
    await prisma.$disconnect()
    process.exit(1)
  })