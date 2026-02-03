import { NextRequest, NextResponse } from 'next/server'
import { AuthService } from '@/lib/auth/auth.service'
import { withAuth, AuthenticatedRequest } from '@/lib/auth/middleware'
import { z } from 'zod'

const changePasswordSchema = z.object({
  currentPassword: z.string().min(1),
  newPassword: z.string().min(6)
})

export const POST = withAuth(async (req: AuthenticatedRequest) => {
  try {
    const body = await req.json()
    
    // Validate input
    const validatedData = changePasswordSchema.parse(body)
    
    // Change password
    await AuthService.changePassword(
      req.user!.id,
      validatedData.currentPassword,
      validatedData.newPassword
    )
    
    return NextResponse.json({
      success: true,
      message: 'Password changed successfully'
    })
  } catch (error: any) {
    console.error('Change password error:', error)
    
    if (error.message.includes('incorrect') || error.message.includes('Invalid')) {
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
      { error: 'Failed to change password' },
      { status: 500 }
    )
  }
})