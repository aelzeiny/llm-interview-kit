"use client";

import React, { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Mic,
  Square,
  ArrowRight,
  Volume2,
  CheckCircle2,
  Clock,
} from "lucide-react";

interface MediaRecorderWithTimeslice extends MediaRecorder {
  start(timeslice?: number): void;
}

const MicrophoneTest: React.FC = () => {
  const router = useRouter();
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [audioURL, setAudioURL] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [hasListenedToAudio, setHasListenedToAudio] = useState<boolean>(false);
  const mediaRecorder = useRef<MediaRecorderWithTimeslice | null>(null);

  const startRecording = async (): Promise<void> => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(
        stream
      ) as MediaRecorderWithTimeslice;
      const chunks: Blob[] = [];

      mediaRecorder.current.ondataavailable = (e: BlobEvent) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      mediaRecorder.current.onstop = () => {
        const blob = new Blob(chunks, { type: "audio/webm" });
        const url = URL.createObjectURL(blob);
        setAudioURL(url);
        setHasListenedToAudio(false);
      };

      mediaRecorder.current.start();
      setIsRecording(true);
      setError("");
    } catch (err) {
      setError("Please allow microphone access to continue");
      console.error("Error accessing microphone:", err);
    }
  };

  const stopRecording = (): void => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop();
      setIsRecording(false);
      mediaRecorder.current.stream.getTracks().forEach((track) => track.stop());
    }
  };

  const handleContinue = (): void => {
    // Preserve any existing query parameters
    const currentParams = window.location.search;
    router.push(`/assess${currentParams}`);
  };

  const handleAudioPlay = (): void => {
    setHasListenedToAudio(true);
  };

  return (
    <div className="max-w-2xl mx-auto bg-zinc-900 rounded-lg shadow-xl overflow-hidden p-8 border border-zinc-800">
      <h3 className="text-2xl font-bold text-center mb-6 text-white">
        Welcome to your assessment
      </h3>

      <div className="mb-8 text-white">
        <h2 className="text-lg font-semibold mb-4">Before you begin:</h2>
        <div className="space-y-6">
          <div className="flex items-start space-x-3">
            <Clock className="w-6 h-6 mt-1 flex-shrink-0 text-primary" />
            <div>
              <p className="font-medium text-white">Put aside 5-10 minutes</p>
              <p className="text-zinc-400">
                This will be a short interview in English. You will not have to
                write code.
              </p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <Volume2 className="w-6 h-6 mt-1 flex-shrink-0 text-primary" />
            <div>
              <p className="font-medium text-white">Test your microphone</p>
              <p className="text-zinc-400">
                Click the microphone button below and say a few words. We
                recommend speaking as you would during the assessment.
              </p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <CheckCircle2 className="w-6 h-6 mt-1 flex-shrink-0 text-primary" />
            <div>
              <p className="font-medium text-white">Proceed when ready</p>
              <p className="text-zinc-400">
                Once you're satisfied with your audio quality, click continue to
                begin the assessment.
              </p>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-destructive/10 border-l-4 border-destructive p-4 mb-6 rounded-md">
          <p className="text-destructive-foreground">{error}</p>
        </div>
      )}

      <div className="space-y-6">
        <div className="flex justify-center">
          {!isRecording ? (
            <button
              onClick={startRecording}
              className="bg-primary text-primary-foreground p-4 rounded-full hover:opacity-90 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ring-offset-background"
              aria-label="Start recording"
            >
              <Mic className="w-8 h-8" />
            </button>
          ) : (
            <button
              onClick={stopRecording}
              className="bg-destructive text-destructive-foreground p-4 rounded-full hover:opacity-90 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ring-offset-background"
              aria-label="Stop recording"
            >
              <Square className="w-8 h-8" />
            </button>
          )}
        </div>

        {audioURL && (
          <div className="flex justify-center">
            <audio
              controls
              src={audioURL}
              className="w-full rounded-md [&::-webkit-media-controls-panel]:bg-muted [&::-webkit-media-controls-current-time-display]:text-foreground [&::-webkit-media-controls-time-remaining-display]:text-foreground"
              onPlay={handleAudioPlay}
            />
          </div>
        )}

        {audioURL && hasListenedToAudio && (
          <div className="flex justify-center mt-6">
            <button
              onClick={handleContinue}
              className="flex items-center space-x-2 bg-secondary text-secondary-foreground px-6 py-3 rounded-md hover:opacity-90 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ring-offset-background"
            >
              <span>Continue to Assessment</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default MicrophoneTest;
