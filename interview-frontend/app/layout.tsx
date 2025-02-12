import "@livekit/components-styles";
import "./globals.css";
import { Public_Sans } from "next/font/google";
import localFont from "next/font/local";

const publicSans400 = Public_Sans({
  weight: "400",
  subsets: ["latin"],
});

const HoneyCombFont = localFont({ src: "./font/honeycomb.woff" });

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`h-full ${publicSans400.className}`}>
      <body className="h-full">
        <div className="min-h-screen py-12 px-4 text-white">
          <h2
            className={`${HoneyCombFont.className} text-white text-center`}
            style={{ fontSize: "5rem" }}
          >
            Hiveminds
          </h2>
          {children}
        </div>
      </body>
    </html>
  );
}
