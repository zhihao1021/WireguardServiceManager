import type { Metadata } from "next";
import { Noto_Sans, Noto_Sans_TC } from "next/font/google";

import "./globals.css"

const notoSans = Noto_Sans({
    variable: "--font-noto-sans",
    subsets: ["latin"],
});

const notoSansTC = Noto_Sans_TC({
    variable: "--font-noto-sans-tc",
    subsets: ["latin"],
});

export const metadata: Metadata = {
    title: "Wireguard Service Manager",
    description: "Automatic assign wireguard client.",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <body className={`${notoSans.className} ${notoSansTC.className}`}>
                {children}
            </body>
        </html>
    );
}
