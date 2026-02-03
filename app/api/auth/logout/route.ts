import { NextRequest, NextResponse } from 'next/server'
import { AuthService } from '@/lib/auth/auth.service'

export async function POST(req: NextRequest) {
  try {
    // Get token from cookie or header
    const token = req.cookies.get('auth-token')?.value || 
                  req.headers.get('authorization')?.replace('Bearer ', '')
    
    if (token) {
      await AuthService.logout(token)
    }
    
    // Clear cookie
    const response = NextResponse.json({
      success: true,
      message: 'Logout successful'
    })
    
    response.cookies.set('auth-token', '', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      expires: new Date(0),
      path: '/'
    })
    
    return response
  } catch (error) {
    console.error('Logout error:', error)
    return NextResponse.json(
      { error: 'Logout failed' },
      { status: 500 }
    )
  }
}