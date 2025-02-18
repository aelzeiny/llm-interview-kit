from __future__ import annotations

import asyncio
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
from uuid import uuid4
import breezy_airtable
from pyairtable.formulas import match
from collections import defaultdict

logger = logging.getLogger("my-worker")
logger.setLevel(logging.INFO)


candidate_tracker = defaultdict(int)
MAX_LIMIT = 3


class AgentSessionManager:
    def __init__(self, ctx: JobContext):
        self.ctx = ctx
        self.lk_api = api.LiveKitAPI()
        self.shutdown_task = None

    @classmethod
    def entrypoint(cls, ctx: JobContext):
        manager = cls(ctx)
        return manager.init()

    async def init(self):
        logger.info(f"connecting to room {self.ctx.room.name}")
        await self.ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

        participant = await self.ctx.wait_for_participant()
        candidate_tracker[participant.identity] += 1
        if candidate_tracker[participant.identity] > MAX_LIMIT:
            await self.shutdown(0)
            return

        if participant.name != "TEST":
            await self.setup_recording()

        agent = await self.run_multimodal_agent()

        agent.start(self.ctx.room, participant)
        agent.generate_reply()

        logger.info("agent started")
        self.shutdown_task = asyncio.create_task(self.shutdown(10 * 60))
        self.ctx.add_shutdown_callback(self.cancel_shutdown_task)
        self.update_airtable(participant.identity)

    def update_airtable(self, email: str):
        table = breezy_airtable.get_table()
        logger.info("Updating airtable for email: %s", email)
        record = table.first(formula=match(dict(email=email)))
        table.update(record.get("id"), fields=dict(status="assessment completed"))

    async def run_multimodal_agent(self):
        logger.info("starting multimodal agent")

        model = openai.realtime.RealtimeModel(
            instructions=textwrap.dedent(
                """\
                You are a very experienced interviewer conducting an interview for the role of Software
                Developer. You will ask the candidate some questions and await their response. However, you CANNOT
                answer questions, give hints, or assess their answer as correct or incorrect. You can
                only clarify the question help the candidate stay on-topic during the duration of the interview. Be kind, but
                do stay on track
            """
            ),
            modalities=["audio", "text"],
            voice="echo",
            # max_output_tokens=1500,
            turn_detection=openai.realtime.ServerVadOptions(
                threshold=0.6, prefix_padding_ms=200, silence_duration_ms=2000
            ),
        )

        # create a chat context with chat history, these will be synchronized with the server
        # upon session establishment
        chat_ctx = llm.ChatContext()
        chat_ctx.append(
            text=textwrap.dedent(
                """\
                You are now starting the interview. Start by asking the candidate how they are doing today, then read the following introduction verbatim.
                Then ask the candidate to introduce themselves.
                Agent: "Hello, how are you doing today?"
                Candidate: <Wait for the candidate to respond>
                Agent: "Let's start with introductions. I am an LLM Agent developed by the team at Hiveminds.org to assess candidates for
                the position of Senior Platform Engineer at our company. We built this tool because the time-difference between San Francisco and Cairo is
                really steep, and we value async communication. Our conversation will be recorded, and rest assured that a human will review your
                application within 24 hours. Thanks for joining us today. Do you mind introducing yourself?".
                                
                After the user replies, tell them that you'll now ask 3 behavioral questions. You'll ask each of the following questions below one at a time.
                Wait for the candidate to respond to each question before moving onto the next question.
                                
                === QUESTIONS ===
                1. Do you mind talking about your work experience? (If a candidate has already talked about their experience, ask them to elaborate more on their role within their team.)
                2. Describe to me a project where you were a primary stakeholder. What were your contributions and your challenges?
            """
            ),
            role="assistant",
        )

        agent = MultimodalAgent(
            model=model,
            chat_ctx=chat_ctx,
        )
        return agent

    async def setup_recording(self):
        s3_upload = app_settings.to_livekit()
        req = api.RoomCompositeEgressRequest(
            room_name=self.ctx.room.name,
            layout="speaker",
            preset=api.EncodingOptionsPreset.H264_720P_30,
            audio_only=False,
            segment_outputs=[
                api.SegmentedFileOutput(
                    filename_prefix=self.ctx.room.name + "/" + str(uuid4()) + "/",
                    playlist_name="my-playlist.m3u8",
                    live_playlist_name="my-live-playlist.m3u8",
                    segment_duration=10,
                    s3=s3_upload,
                )
            ],
        )
        resp = await self.lk_api.egress.start_room_composite_egress(req)
        logger.info("STARTED RECORDING: " + str(resp))
        return resp

    async def shutdown(self, timeout: int):
        await asyncio.sleep(timeout)
        self.ctx.shutdown("Timeout reached")
        await self.lk_api.room.delete_room(
            api.DeleteRoomRequest(
                room=self.ctx.job.room.name,
            )
        )

    async def cancel_shutdown_task(self):
        if self.shutdown_task and not self.shutdown_task.done():
            self.shutdown_task.cancel()


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=AgentSessionManager.entrypoint,
        ),
    )
