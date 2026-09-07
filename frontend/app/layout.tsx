import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = { title: 'NahaLabs Content OS', description: 'Shoot once. Get a month of content.' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
