import { NextResponse, type NextRequest } from 'next/server';
import { createServerClient, type CookieOptions } from '@supabase/ssr';

/**
 * Session refresh and the authentication boundary.
 *
 * When Supabase Auth is configured, every page requires a session and this
 * refreshes the token on each request. When it is not, the studio runs as a
 * single local owner and the middleware stands aside — the Security Checklist
 * reports which of the two is in force rather than leaving it ambiguous.
 *
 * `/api/jobs/run` is exempt because it authenticates differently: an HMAC over
 * the request body, which is the right shape for a platform cron and the wrong
 * shape for a cookie.
 */
export async function middleware(request: NextRequest) {
  const url = process.env.SUPABASE_URL;
  const anon = process.env.SUPABASE_ANON_KEY;
  if (!url || !anon) return NextResponse.next();

  let response = NextResponse.next({ request });

  const supabase = createServerClient(url, anon, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll: (list: Array<{ name: string; value: string; options: CookieOptions }>) => {
        for (const c of list) request.cookies.set(c.name, c.value);
        response = NextResponse.next({ request });
        for (const c of list) response.cookies.set(c.name, c.value, c.options);
      },
    },
  });

  const { data } = await supabase.auth.getUser();
  const path = request.nextUrl.pathname;
  const isPublic = path === '/login' || path.startsWith('/api/jobs/');

  if (!data.user && !isPublic) {
    const to = request.nextUrl.clone();
    to.pathname = '/login';
    to.search = '';
    return NextResponse.redirect(to);
  }
  return response;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
