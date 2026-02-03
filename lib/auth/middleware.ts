import { NextRequest, NextResponse } from 'next/server'
import { AuthService } from './auth.service'

export interface AuthenticatedRequest extends NextRequest {
  user?: any
}

export function withAuth(handler: (req: AuthenticatedRequest) => Promise<NextResponse>) {
  return async (req: AuthenticatedRequest) => {
    try {
      const token = req.headers.get('authorization')?.replace('Bearer ', '')
      
      if (!token) {
        return NextResponse.json(
          { error: 'Authentication required' },
          { status: 401 }
        )
      }

      const user = await AuthService.getUserByToken(token)
      
      if (!user) {
        return NextResponse.json(
          { error: 'Invalid or expired token' },
          { status: 401 }
        )
      }

      req.user = user
      return await handler(req)
    } catch (error) {
      console.error('Auth middleware error:', error)
      return NextResponse.json(
        { error: 'Authentication failed' },
        { status: 500 }
      )
    }
  }
}

export function optionalAuth(handler: (req: AuthenticatedRequest) => Promise<NextResponse>) {
  return async (req: AuthenticatedRequest) => {
    try {
      const token = req.headers.get('authorization')?.replace('Bearer ', '')
      
      if (token) {
        const user = await AuthService.getUserByToken(token)
        if (user) {
          req.user = user
        }
      }
      
      return await handler(req)
    } catch (error) {
      console.error('Optional auth middleware error:', error)
      return await handler(req) // Continue without auth on error
    }
  }
}