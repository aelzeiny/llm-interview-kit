"use client";

import { AnimatePresence, motion } from "framer-motion";
import {
  LiveKitRoom,
  useVoiceAssistant,
  BarVisualizer,
  RoomAudioRenderer,
  VoiceAssistantControlBar,
  AgentState,
  DisconnectButton,
} from "@livekit/components-react";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { NoAgentNotification } from "@/components/NoAgentNotification";
import { CloseIcon } from "@/components/CloseIcon";
import { useKrispNoiseFilter } from "@livekit/components-react/krisp";
import type { ClaimGrants } from "livekit-server-sdk";
import { MediaDeviceFailure } from "livekit-client";
import localFont from "next/font/local";

const HoneyCombFont = localFont({ src: "./font/honeycomb.woff" });

function Page() {
  const [claims, updateClaims] = useState<ClaimGrants | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [agentState, setAgentState] = useState<AgentState>("disconnected");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isStarted, setIsStarted] = useState<boolean | null>(false);
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  useEffect(() => {
    const fetchClaims = async () => {
      const token = searchParams.get("token");
      if (!token) {
        setError("Unauthorized: No Token provided");
        return;
      }
      const url = new URL(
        process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT ?? "/api/verify",
        window.location.origin
      );
      const response = await fetch(url.toString(), {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      const newClaims = await response.json();
      setIsLoading(false);
      if (newClaims.error) {
        setError(newClaims.error);
      } else {
        updateClaims(newClaims);
      }
    };
    fetchClaims();
  }, [searchParams]);

  const onConnectButtonClicked = () => {
    setIsStarted(true);
  };

  return (
    <main
      data-lk-theme="default"
      className="h-full grid content-center bg-[var(--lk-bg)]"
    >
      <div style={{ textAlign: "center" }}>
        <h2 className={HoneyCombFont.className} style={{ fontSize: "5rem" }}>
          Hiveminds
        </h2>
        {isLoading && <h3>Loading...</h3>}
        {error && <h3>Error: {error}</h3>}
        {claims && <h3>Hello {claims?.name}</h3>}
        {isStarted === null && (
          <p>
            Thank you for taking the assessment. We&apos;ll get back to you in
            24 hours. <br />
            If there was an issue then please do not hesitate to email us back
            or try refreshing the page.
            <br />
          </p>
        )}
      </div>

      {!isLoading && !error && isStarted !== null && (
        <>
          <LiveKitRoom
            token={token!}
            serverUrl={process.env.NEXT_PUBLIC_LIVEKIT_URL}
            connect={isStarted === true}
            audio={true}
            video={false}
            onMediaDeviceFailure={onDeviceFailure}
            onDisconnected={() => {
              setIsStarted(null);
            }}
            className="grid grid-rows-[2fr_1fr] items-center"
          >
            <SimpleVoiceAssistant onStateChange={setAgentState} />
            <ControlBar
              onConnectButtonClicked={onConnectButtonClicked}
              agentState={agentState}
            />
            <RoomAudioRenderer />
            <NoAgentNotification state={agentState} />
          </LiveKitRoom>
        </>
      )}
    </main>
  );
}

function SimpleVoiceAssistant(props: {
  onStateChange: (state: AgentState) => void;
}) {
  const { state, audioTrack } = useVoiceAssistant();
  useEffect(() => {
    props.onStateChange(state);
  }, [props, state]);
  return (
    <div className="h-[300px] max-w-[90vw] mx-auto">
      <BarVisualizer
        state={state}
        barCount={5}
        trackRef={audioTrack}
        className="agent-visualizer"
        options={{ minHeight: 24 }}
      />
    </div>
  );
}

function ControlBar(props: {
  onConnectButtonClicked: () => void;
  agentState: AgentState;
}) {
  /**
   * Use Krisp background noise reduction when available.
   * Note: This is only available on Scale plan, see {@link https://livekit.io/pricing | LiveKit Pricing} for more details.
   */
  const krisp = useKrispNoiseFilter();
  useEffect(() => {
    krisp.setNoiseFilterEnabled(true);
  }, []);

  return (
    <div className="relative h-[100px]">
      <AnimatePresence>
        {props.agentState === "disconnected" && (
          <motion.button
            initial={{ opacity: 0, top: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, top: "-10px" }}
            transition={{ duration: 1, ease: [0.09, 1.04, 0.245, 1.055] }}
            className="uppercase absolute left-1/2 -translate-x-1/2 px-4 py-2 bg-white text-black rounded-md"
            onClick={() => props.onConnectButtonClicked()}
          >
            Begin Assessment
          </motion.button>
        )}
      </AnimatePresence>
      <AnimatePresence>
        {props.agentState !== "disconnected" &&
          props.agentState !== "connecting" && (
            <motion.div
              initial={{ opacity: 0, top: "10px" }}
              animate={{ opacity: 1, top: 0 }}
              exit={{ opacity: 0, top: "-10px" }}
              transition={{ duration: 0.4, ease: [0.09, 1.04, 0.245, 1.055] }}
              className="flex h-8 absolute left-1/2 -translate-x-1/2  justify-center"
            >
              <VoiceAssistantControlBar controls={{ leave: false }} />
              <DisconnectButton>
                <CloseIcon />
              </DisconnectButton>
            </motion.div>
          )}
      </AnimatePresence>
    </div>
  );
}

function onDeviceFailure(error?: MediaDeviceFailure) {
  console.error(error);
  alert(
    "Error acquiring camera or microphone permissions. Please make sure you grant the necessary permissions in your browser and reload the tab"
  );
}

export default function SuspendedPage() {
  return (
    <Suspense fallback={<h2>Loading...</h2>}>
      <Page />
    </Suspense>
  );
}
