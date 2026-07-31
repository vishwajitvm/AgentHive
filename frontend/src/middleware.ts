import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname
  
  // Define public paths
  const isPublicPath = path === '/login' || path === '/signup' || path === '/verify'
  
  // In a real app we'd verify the JWT token here, but for this local agenthive 
  // implementation we check for the presence of the token in cookies or localStorage.
  // Since we can't easily read localStorage in middleware, we expect the frontend 
  // to set a cookie upon login.
  const token = request.cookies.get('agenthive_token')?.value || ''
  
  if (isPublicPath && token) {
    return NextResponse.redirect(new URL('/agents', request.nextUrl))
  }
  
  if (!isPublicPath && !token && path !== '/' && !path.startsWith('/api') && !path.startsWith('/_next')) {
    return NextResponse.redirect(new URL('/login', request.nextUrl))
  }
  
  return NextResponse.next()
}

export const config = {
  matcher: [
    '/',
    '/login',
    '/signup',
    '/verify',
    '/agents/:path*',
    '/workflows/:path*',
    '/settings/:path*',
  ]
}
