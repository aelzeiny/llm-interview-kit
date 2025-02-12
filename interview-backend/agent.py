from __future__ import annotations

import logging
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.multimodal import MultimodalAgent
from livekit.plugins import openai
import textwrap
from livekit import api
import app_settings


logger = logging.getLogger("my-worker")
logger.setLevel(logging.INFO)


async def setup_recording(ctx: JobContext):
    lk_api = api.LiveKitAPI()
    api.access_token.TokenVerifier
    s3_upload = app_settings.to_livekit()
    req = api.RoomCompositeEgressRequest(
        room_name=ctx.room.name,
        layout="speaker",
        preset=api.EncodingOptionsPreset.H264_720P_30,
        audio_only=False,
        segment_outputs=[
            api.SegmentedFileOutput(
                filename_prefix=ctx.room.name + "/",
                playlist_name="my-playlist.m3u8",
                live_playlist_name="my-live-playlist.m3u8",
                segment_duration=10,
                s3=s3_upload,
            )
        ],
    )
    resp = await lk_api.egress.start_room_composite_egress(req)
    logger.info("STARTED RECORDING: " + str(resp))
    return resp


async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()
    await setup_recording(ctx)

    agent = run_multimodal_agent(ctx, participant)

    agent.start(ctx.room, participant)
    agent.generate_reply()

    logger.info("agent started")


def run_multimodal_agent(ctx: JobContext, participant: rtc.RemoteParticipant):
    logger.info("starting multimodal agent")

    model = openai.realtime.RealtimeModel(
        instructions=textwrap.dedent(
            """\
            You are a very experienced interviewer conducting an interview for the role of Senior Software
            Developer. You will ask the candidate some questions and await their response. However, you CANNOT
            answer questions, give hints, or assess their answer as correct or incorrect. You can
            only clarify the question help the candidate stay on-topic during the duration of the interview.
        """
        ),
        modalities=["audio", "text"],
        voice="echo",
        # max_output_tokens=1500,
        # turn_detection=openai.realtime.ServerVadOptions(
        #     threshold=0.6, prefix_padding_ms=200, silence_duration_ms=2000
        # ),
    )

    # create a chat context with chat history, these will be synchronized with the server
    # upon session establishment
    chat_ctx = llm.ChatContext()
    chat_ctx.append(
        text=textwrap.dedent(
            """\
            You are now starting the interview. Start by reading the following introduction verbatim. Then ask the candidate to introduce themselves.
            Introduction: "Hello, let's start with introductions. I am an LLM Agent developed by the team at Hiveminds.org to assess candidates for
            the position of Senior Platform Engineer at our company. We built this tool because the time-difference between San Francisco and Cairo is
            really steep, and we value async communication. Our conversation will be recorded, and rest assured that a human will review your
            application within 24 hours. Thanks for joining us today. Do you mind introducing yourself and talking about your work experience?".
                             
            After the user replies, tell them that you'll now ask 5 system architecture questions. You'll ask each of the following questions below one at a time.
            Wait for the candidate to respond to each question before moving onto the next question.
                             
            === QUESTIONS ===
            1. What are relational databases and what are some popular ones used in the cloud?
            2. What are load balancers and what are some popular ones used in the cloud?
            3. What are CDNs and what are some popular ones used in the cloud?
            4. What are server-side caches and what are some popular ones used in the cloud?
            5. What are NoSQL or non-relational databases and what are some popular ones used in the cloud?
                             
            At the end of the interview, thank them for their time then disconnect promptly.
        """
        ),
        role="assistant",
    )

    agent = MultimodalAgent(
        model=model,
        chat_ctx=chat_ctx,
    )
    return agent


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        ),
    )
