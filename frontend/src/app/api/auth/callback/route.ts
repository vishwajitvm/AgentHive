import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const code = searchParams.get('code');
  
  if (!code) {
    return NextResponse.redirect(new URL('/login?error=MissingCode', request.url));
  }

  try {
    // Exchange the code for a token from Keycloak
    const tokenResponse = await fetch('http://keycloak:8080/realms/agenthive/protocol/openid-connect/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        client_id: 'agenthive-frontend',
        code: code,
        redirect_uri: 'http://localhost:3000/api/auth/callback',
      }),
    });

    if (!tokenResponse.ok) {
      const errorData = await tokenResponse.text();
      console.error('Token exchange failed:', errorData);
      return NextResponse.redirect(new URL(`/login?error=TokenExchangeFailed`, request.url));
    }

    const data = await tokenResponse.json();
    const accessToken = data.access_token;
    const idToken = data.id_token;

    // Create a response that redirects to the dashboard safely on localhost
    const response = NextResponse.redirect('http://localhost:3000/agents');
    
    // Set the cookie for the frontend middleware to use
    response.cookies.set('agenthive_token', accessToken, {
      path: '/',
      maxAge: 86400,
      sameSite: 'lax',
      secure: process.env.NODE_ENV === 'production',
    });

    if (idToken) {
      response.cookies.set('agenthive_id_token', idToken, {
        path: '/',
        maxAge: 86400,
        sameSite: 'lax',
        secure: process.env.NODE_ENV === 'production',
      });
    }

    return response;
  } catch (error) {
    console.error('Auth callback error:', error);
    return NextResponse.redirect(new URL('/login?error=InternalError', request.url));
  }
}
