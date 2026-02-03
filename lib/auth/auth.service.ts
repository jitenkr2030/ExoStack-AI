import bcrypt from 'bcryptjs'
import jwt from 'jsonwebtoken'
import { prisma } from '../db'

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key-change-in-production'
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '7d'

export interface AuthUser {
  id: string
  email: string
  username: string
  firstName?: string
  lastName?: string
  avatar?: string
  emailVerified: boolean
  isPremium: boolean
  maxNodes: number
  maxTasks: number
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  username: string
  password: string
  firstName?: string
  lastName?: string
}

export interface AuthResult {
  user: AuthUser
  token: string
  expiresAt: Date
}

export class AuthService {
  static async hashPassword(password: string): Promise<string> {
    return bcrypt.hash(password, 12)
  }

  static async verifyPassword(password: string, hashedPassword: string): Promise<boolean> {
    return bcrypt.compare(password, hashedPassword)
  }

  static generateToken(userId: string): { token: string; expiresAt: Date } {
    const expiresAt = new Date()
    expiresAt.setDate(expiresAt.getDate() + 7) // 7 days from now

    const token = jwt.sign(
      { 
        userId,
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(expiresAt.getTime() / 1000)
      },
      JWT_SECRET
    )

    return { token, expiresAt }
  }

  static verifyToken(token: string): { userId: string } | null {
    try {
      const decoded = jwt.verify(token, JWT_SECRET) as { userId: string }
      return decoded
    } catch (error) {
      return null
    }
  }

  static async register(data: RegisterData): Promise<AuthResult> {
    // Check if user already exists
    const existingUser = await prisma.user.findFirst({
      where: {
        OR: [
          { email: data.email },
          { username: data.username }
        ]
      }
    })

    if (existingUser) {
      if (existingUser.email === data.email) {
        throw new Error('Email already registered')
      }
      if (existingUser.username === data.username) {
        throw new Error('Username already taken')
      }
    }

    // Hash password
    const hashedPassword = await this.hashPassword(data.password)

    // Create user
    const user = await prisma.user.create({
      data: {
        email: data.email,
        username: data.username,
        password: hashedPassword,
        firstName: data.firstName,
        lastName: data.lastName,
        loginCount: 1,
        lastLogin: new Date()
      }
    })

    // Create user profile
    await prisma.userProfile.create({
      data: {
        userId: user.id
      }
    })

    // Generate token
    const { token, expiresAt } = this.generateToken(user.id)

    // Create session
    await prisma.session.create({
      data: {
        userId: user.id,
        token,
        expiresAt
      }
    })

    // Log registration
    await prisma.auditLog.create({
      data: {
        userId: user.id,
        action: 'register',
        resource: 'user',
        resourceId: user.id
      }
    })

    return {
      user: this.sanitizeUser(user),
      token,
      expiresAt
    }
  }

  static async login(credentials: LoginCredentials): Promise<AuthResult> {
    // Find user by email
    const user = await prisma.user.findUnique({
      where: { email: credentials.email },
      include: { profile: true }
    })

    if (!user) {
      throw new Error('Invalid credentials')
    }

    if (!user.isActive) {
      throw new Error('Account is deactivated')
    }

    // Verify password
    const isValidPassword = await this.verifyPassword(credentials.password, user.password)
    if (!isValidPassword) {
      throw new Error('Invalid credentials')
    }

    // Update login stats
    await prisma.user.update({
      where: { id: user.id },
      data: {
        lastLogin: new Date(),
        loginCount: user.loginCount + 1
      }
    })

    // Generate token
    const { token, expiresAt } = this.generateToken(user.id)

    // Create session
    await prisma.session.create({
      data: {
        userId: user.id,
        token,
        expiresAt
      }
    })

    // Log login
    await prisma.auditLog.create({
      data: {
        userId: user.id,
        action: 'login',
        resource: 'user',
        resourceId: user.id
      }
    })

    return {
      user: this.sanitizeUser(user),
      token,
      expiresAt
    }
  }

  static async logout(token: string): Promise<void> {
    // Remove session
    await prisma.session.deleteMany({
      where: { token }
    })

    // Get user ID from token for logging
    const decoded = this.verifyToken(token)
    if (decoded) {
      await prisma.auditLog.create({
        data: {
          userId: decoded.userId,
          action: 'logout',
          resource: 'user',
          resourceId: decoded.userId
        }
      })
    }
  }

  static async getUserByToken(token: string): Promise<AuthUser | null> {
    // Verify token
    const decoded = this.verifyToken(token)
    if (!decoded) {
      return null
    }

    // Check if session exists and is not expired
    const session = await prisma.session.findUnique({
      where: { token },
      include: { user: true }
    })

    if (!session || session.expiresAt < new Date()) {
      return null
    }

    // Update last activity
    await prisma.session.update({
      where: { id: session.id },
      data: { lastActivity: new Date() }
    })

    return this.sanitizeUser(session.user)
  }

  static async changePassword(userId: string, currentPassword: string, newPassword: string): Promise<void> {
    const user = await prisma.user.findUnique({
      where: { id: userId }
    })

    if (!user) {
      throw new Error('User not found')
    }

    // Verify current password
    const isValidPassword = await this.verifyPassword(currentPassword, user.password)
    if (!isValidPassword) {
      throw new Error('Current password is incorrect')
    }

    // Hash new password
    const hashedNewPassword = await this.hashPassword(newPassword)

    // Update password
    await prisma.user.update({
      where: { id: userId },
      data: { password: hashedNewPassword }
    })

    // Log password change
    await prisma.auditLog.create({
      data: {
        userId,
        action: 'change_password',
        resource: 'user',
        resourceId: userId
      }
    })

    // Invalidate all other sessions
    await prisma.session.deleteMany({
      where: {
        userId,
        NOT: { token: '' } // This will be updated with current session token
      }
    })
  }

  static async updateProfile(userId: string, data: Partial<{
    firstName: string
    lastName: string
    avatar: string
    bio: string
    company: string
    location: string
    website: string
    github: string
    twitter: string
    linkedin: string
    theme: string
    emailDigest: boolean
    taskNotifications: boolean
    nodeAlerts: boolean
  }>): Promise<AuthUser> {
    const user = await prisma.user.update({
      where: { id: userId },
      data: {
        ...(data.firstName && { firstName: data.firstName }),
        ...(data.lastName && { lastName: data.lastName }),
        ...(data.avatar !== undefined && { avatar: data.avatar })
      },
      include: { profile: true }
    })

    // Update profile if provided
    if (data.bio !== undefined || data.company !== undefined || data.location !== undefined ||
        data.website !== undefined || data.github !== undefined || data.twitter !== undefined ||
        data.linkedin !== undefined || data.theme !== undefined || data.emailDigest !== undefined ||
        data.taskNotifications !== undefined || data.nodeAlerts !== undefined) {
      
      await prisma.userProfile.update({
        where: { userId },
        data: {
          ...(data.bio !== undefined && { bio: data.bio }),
          ...(data.company !== undefined && { company: data.company }),
          ...(data.location !== undefined && { location: data.location }),
          ...(data.website !== undefined && { website: data.website }),
          ...(data.github !== undefined && { github: data.github }),
          ...(data.twitter !== undefined && { twitter: data.twitter }),
          ...(data.linkedin !== undefined && { linkedin: data.linkedin }),
          ...(data.theme !== undefined && { theme: data.theme }),
          ...(data.emailDigest !== undefined && { emailDigest: data.emailDigest }),
          ...(data.taskNotifications !== undefined && { taskNotifications: data.taskNotifications }),
          ...(data.nodeAlerts !== undefined && { nodeAlerts: data.nodeAlerts })
        }
      })
    }

    // Log profile update
    await prisma.auditLog.create({
      data: {
        userId,
        action: 'update_profile',
        resource: 'user',
        resourceId: userId,
        details: data as any
      }
    })

    return this.sanitizeUser(user)
  }

  private static sanitizeUser(user: any): AuthUser {
    return {
      id: user.id,
      email: user.email,
      username: user.username,
      firstName: user.firstName,
      lastName: user.lastName,
      avatar: user.avatar,
      emailVerified: user.emailVerified,
      isPremium: user.isPremium,
      maxNodes: user.maxNodes,
      maxTasks: user.maxTasks
    }
  }

  static async cleanupExpiredSessions(): Promise<void> {
    await prisma.session.deleteMany({
      where: {
        expiresAt: {
          lt: new Date()
        }
      }
    })
  }
}