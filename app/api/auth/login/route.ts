import { NextRequest, NextResponse } from 'next/server'
import { AuthService, LoginCredentials } from '@/lib/auth/auth.service'
import { z } from 'zod'

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1)
})

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    
    // Validate input
    const validatedData = loginSchema.parse(body)
    
    // Login user
    const result = await AuthService.login(validatedData as LoginCredentials)
    
    // Set HTTP-only cookie with token
    const response = NextResponse.json({
      success: true,
      user: result.user,
      message: 'Login successful'
    })
    
    response.cookies.set('auth-token', result.token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      expires: result.expiresAt,
      path: '/'
    })
    
    return response
  } catch (error: any) {
    console.error('Login error:', error)
    
    if (error.message.includes('Invalid') || error.message.includes('deactivated')) {
      return NextResponse.json(
        { error: error.message },
        { status: 401 }
      )
    }
    
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Invalid input data', details: error.errors },
        { status: 400 }
      )
    }
    
    return NextResponse.json(
      { error: 'Login failed' },
      { status: 500 }
    )
  }
}