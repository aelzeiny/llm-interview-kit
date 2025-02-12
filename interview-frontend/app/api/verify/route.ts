// ./app/api/verify-jwt/route.ts
import { NextRequest, NextResponse } from "next/server";
import { TokenVerifier } from "livekit-server-sdk";

// NOTE: you are expected to define the following environment variables in `.env.local`:
const API_KEY = process.env.LIVEKIT_API_KEY!;
const API_SECRET = process.env.LIVEKIT_API_SECRET!;

// don't cache the results
export const revalidate = 0;

async function verifyToken(token: string) {
  try {
    const verifier = new TokenVerifier(API_KEY, API_SECRET);
    return await verifier.verify(token);
  } catch {
    return null;
  }
}

export async function GET(request: NextRequest) {
  const authHeader = request.headers.get("authorization");

  if (!authHeader) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const token = authHeader.substring("Bearer".length).trimStart();
  const claims = await verifyToken(token);

  if (!claims) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  return NextResponse.json(claims);
}
