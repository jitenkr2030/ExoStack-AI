import { NextRequest, NextResponse } from 'next/server'
import { AuthService } from '@/lib/auth/auth.service'
import { withAuth, AuthenticatedRequest } from '@/lib/auth/middleware'
import { z } from 'zod'

const updateProfileSchema = z.object({
  firstName: z.string().optional(),
  lastName: z.string().optional(),
  avatar: z.string().url().optional(),
  bio: z.string().optional(),
  company: z.string().optional(),
  location: z.string().optional(),
  website: z.string().url().optional(),
  github: z.string().optional(),
  twitter: z.string().optional(),
  linkedin: z.string().optional(),
  theme: z.enum(['light', 'dark']).optional(),
  emailDigest: z.boolean().optional(),
  taskNotifications: z.boolean().optional(),
  nodeAlerts: z.boolean().optional()
})

const changePasswordSchema = z.object({
  currentPassword: z.string().min(1),
  newPassword: z.string().min(6)
})

export const GET = withAuth(async (req: AuthenticatedRequest) => {
  try {
    // Get full user profile with additional details
    const { prisma } = await import('@/lib/db')
    
    const user = await prisma.user.findUnique({
      where: { id: req.user!.id },
      include: {
        profile: true,
        nodes: {
          select: {
            id: true,
            name: true,
            status: true,
            readinessScore: true,
            lastSeen: true
          }
        },
        _count: {
          select: {
            nodes: true,
            tasks: true
          }
        }
      }
    })

    if (!user) {
      return NextResponse.json(
        { error: 'User not found' },
        { status: 404 }
      )
    }

    return NextResponse.json({
      success: true,
      user: {
        id: user.id,
        email: user.email,
        username: user.username,
        firstName: user.firstName,
        lastName: user.lastName,
        avatar: user.avatar,
        emailVerified: user.emailVerified,
        isPremium: user.isPremium,
        maxNodes: user.maxNodes,
        maxTasks: user.maxTasks,
        createdAt: user.createdAt,
        lastLogin: user.lastLogin,
        loginCount: user.loginCount,
        profile: user.profile,
        nodes: user.nodes,
        stats: {
          totalNodes: user._count.nodes,
          totalTasks: user._count.tasks
        }
      }
    })
  } catch (error) {
    console.error('Get user profile error:', error)
    return NextResponse.json(
      { error: 'Failed to get user profile' },
      { status: 500 }
    )
  }
})

export const PUT = withAuth(async (req: AuthenticatedRequest) => {
  try {
    const body = await req.json()
    
    // Validate input
    const validatedData = updateProfileSchema.parse(body)
    
    // Update user profile
    const updatedUser = await AuthService.updateProfile(req.user!.id, validatedData)
    
    return NextResponse.json({
      success: true,
      user: updatedUser,
      message: 'Profile updated successfully'
    })
  } catch (error: any) {
    console.error('Update profile error:', error)
    
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Invalid input data', details: error.errors },
        { status: 400 }
      )
    }
    
    return NextResponse.json(
      { error: error.message || 'Failed to update profile' },
      { status: 500 }
    )
  }
})