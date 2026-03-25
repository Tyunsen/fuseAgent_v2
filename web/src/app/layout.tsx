import { Toaster } from '@/components/ui/sonner';
import { getServerApi } from '@/lib/api/server';
import { getLocale } from '@/services/cookies';
import type { Metadata } from 'next';
import { NextIntlClientProvider } from 'next-intl';
import { Geist, Geist_Mono } from 'next/font/google';
import NextTopLoader from 'nextjs-toploader';

import { AppProvider } from '@/components/providers/app-provider';
import { ThemeProvider } from '@/components/providers/theme-provider';
import 'highlight.js/styles/github-dark.css';
import './globals.css';

import { getTranslations } from 'next-intl/server';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export async function generateMetadata(): Promise<Metadata> {
  const common_site = await getTranslations('common.site');
  const appName =
    process.env.NEXT_PUBLIC_APP_NAME || common_site('metadata.title');
  const appDescription =
    process.env.NEXT_PUBLIC_APP_DESCRIPTION ||
    common_site('metadata.description');
  const authorName =
    process.env.NEXT_PUBLIC_APP_AUTHOR_NAME ||
    common_site('metadata.authors.name');
  const authorUrl =
    process.env.NEXT_PUBLIC_APP_AUTHOR_URL ||
    common_site('metadata.authors.url');

  return {
    applicationName: appName,
    authors: {
      name: authorName,
      url: authorUrl,
    },
    title: {
      default: appName,
      template: `%s | ${appName}`,
    },
    description: appDescription,
    keywords: ['RAG', 'Graph Search', 'Vector Search', 'Full-Text Search'],
  };
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const locale = await getLocale();
  let user;
  const apiServer = await getServerApi();
  try {
    const res = await apiServer.defaultApi.userGet();
    user = res.data;
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
  } catch (err) {}

  return (
    <html lang={locale} suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <NextTopLoader
          // color="color-mix(in oklab, var(--primary), transparent)"
          color="var(--primary)"
          showSpinner={false}
          crawl={false}
        />
        <NextIntlClientProvider>
          <ThemeProvider
            attribute="class"
            defaultTheme={process.env.NEXT_PUBLIC_DEFAULT_THEME || 'system'}
            enableSystem
            disableTransitionOnChange
          >
            <Toaster position="top-center" richColors />
            <AppProvider user={user}>{children}</AppProvider>
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
