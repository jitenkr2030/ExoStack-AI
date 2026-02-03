import { NextRequest, NextResponse } from 'next/server'
import { AuthService } from '@/lib/auth/auth.service'

export async function GET(req: NextRequest) {
  try {
    // Get token from cookie or header
    const token = req.cookies.get('auth-token')?.value || 
                  req.headers.get('authorization')?.replace('Bearer ', '')
    
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
    
    return NextResponse.json({
      success: true,
      user
    })
  } catch (error) {
    console.error('Get user error:', error)
    return NextResponse.json(
      { error: 'Failed to get user information' },
      { status: 500 }
    )
  }
}