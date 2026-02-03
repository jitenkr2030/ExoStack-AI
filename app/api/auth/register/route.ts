import { NextRequest, NextResponse } from 'next/server'
import { AuthService, RegisterData } from '@/lib/auth/auth.service'
import { z } from 'zod'

const registerSchema = z.object({
  email: z.string().email(),
  username: z.string().min(3).max(20),
  password: z.string().min(6),
  firstName: z.string().optional(),
  lastName: z.string().optional()
})

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    
    // Validate input
    const validatedData = registerSchema.parse(body)
    
    // Register user
    const result = await AuthService.register(validatedData as RegisterData)
    
    // Set HTTP-only cookie with token
    const response = NextResponse.json({
      success: true,
      user: result.user,
      message: 'Registration successful'
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
    console.error('Registration error:', error)
    
    if (error.message.includes('already') || error.message.includes('taken')) {
      return NextResponse.json(
        { error: error.message },
        { status: 400 }
      )
    }
    
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Invalid input data', details: error.errors },
        { status: 400 }
      )
    }
    
    return NextResponse.json(
      { error: 'Registration failed' },
      { status: 500 }
    )
  }
}