import { NextRequest, NextResponse } from 'next/server'
import { AuthService } from '@/lib/auth/auth.service'

// Paths that don't require authentication
const publicPaths = ['/', '/api/auth/login', '/api/auth/register']

// Paths that require authentication
const protectedPaths = ['/dashboard', '/api/user', '/api/nodes', '/api/tasks']

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl

  // Allow public paths
  if (publicPaths.some(path => pathname.startsWith(path))) {
    return NextResponse.next()
  }

  // Check if path requires authentication
  if (protectedPaths.some(path => pathname.startsWith(path))) {
    // Get token from cookie or header
    const token = req.cookies.get('auth-token')?.value || 
                  req.headers.get('authorization')?.replace('Bearer ', '')

    if (!token) {
      // Redirect to login for protected pages
      if (pathname.startsWith('/dashboard')) {
        return NextResponse.redirect(new URL('/', req.url))
      }
      // Return 401 for API routes
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      )
    }

    // Verify token
    const user = await AuthService.getUserByToken(token)
    if (!user) {
      // Clear invalid token
      const response = pathname.startsWith('/dashboard') 
        ? NextResponse.redirect(new URL('/', req.url))
        : NextResponse.json(
            { error: 'Invalid or expired token' },
            { status: 401 }
          )

      response.cookies.set('auth-token', '', {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        expires: new Date(0),
        path: '/'
      })

      return response
    }

    // Add user to request headers for API routes
    if (pathname.startsWith('/api/')) {
      const requestHeaders = new Headers(req.headers)
      requestHeaders.set('x-user-id', user.id)
      requestHeaders.set('x-user-email', user.email)

      return NextResponse.next({
        request: {
          headers: requestHeaders,
        },
      })
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public (public files)
     */
    '/((?!_next/static|_next/image|favicon.ico|public).*)',
  ],
}