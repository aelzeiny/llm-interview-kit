import { NextRequest, NextResponse } from "next/server";
import {
  AccessToken,
  AccessTokenOptions,
  VideoGrant,
} from "livekit-server-sdk";

// NOTE: you are expected to define the following environment variables in `.env.local`:
const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const CUSTOM_API_SECRET = process.env.CUSTOM_API_SECRET;

// don't cache the results
export const revalidate = 0;

export type ConnectionDetails = {
  roomName: string;
  participantName: string;
  participantToken: string;
};

function createParticipantToken(
  userInfo: AccessTokenOptions,
  roomName: string
) {
  const at = new AccessToken(API_KEY, API_SECRET, {
    ...userInfo,
    ttl: "7d",
  });
  const grant: VideoGrant = {
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  };
  at.addGrant(grant);
  return at.toJwt();
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const name = searchParams.get("name");
  const email = searchParams.get("email");

  if (request.headers.get("authorization") !== CUSTOM_API_SECRET) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const roomName = `voice_assistant_room_${email?.replaceAll("@", "-")}`;
  const participantToken = await createParticipantToken(
    { identity: email || undefined, name: name || undefined },
    roomName
  );

  return NextResponse.json({ jwt: participantToken });
}
