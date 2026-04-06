import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Gold Trading Agent',
  description: 'Real-time XAU/USD analysis with technical indicators',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-white">{children}</body>
    </html>
  )
}
