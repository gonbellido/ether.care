"""
Esoter Therapist - LiveKit Voice Agent
=======================================
Agente de voz en tiempo real que:
  - Escucha al usuario (Deepgram STT en español)
  - Envía la transcripción a n8n (cerebro/RAG/agentes)
  - Reproduce la respuesta con Cartesia TTS (voz española)

Compatible con livekit-agents 1.x
"""

import logging
import os
from typing import AsyncIterator

import aiohttp
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
    llm as agents_llm,
)
from livekit.plugins import cartesia, openai, silero

# ─── Configuración ────────────────────────────────────────────
logger = logging.getLogger("esoter-agent")
logging.basicConfig(level=logging.INFO)

N8N_WEBHOOK_URL = os.environ.get(
    "N8N_WEBHOOK_URL",
    "http://n8n:5678/webhook/e8441923-ad2d-4b62-af61-85ef0c42aa79",
)
N8N_TIMEOUT = int(os.environ.get("N8N_TIMEOUT", "30"))

CARTESIA_API_KEY = os.environ.get("CARTESIA_API_KEY", "")
CARTESIA_VOICE_ID = os.environ.get(
    "CARTESIA_VOICE_ID",
    "13ff5deb-2591-42ad-a356-63a04e524411",
)

WHISPER_URL = os.environ.get("WHISPER_URL", "http://whisper:8080/v1")


# ─── LLM personalizado que llama a n8n ────────────────────────
class N8NLLM(agents_llm.LLM):
    """
    Wrapper que hace pasar a n8n como si fuera un LLM.
    LiveKit envía la transcripción aquí, n8n procesa con su RAG/agentes
    y devuelve texto que LiveKit manda al TTS.
    """

    def __init__(self, webhook_url: str, timeout: int = 30):
        super().__init__()
        self._webhook_url = webhook_url
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self._session

    async def aclose(self):
        if self._session and not self._session.closed:
            await self._session.close()

    def chat(
        self,
        *,
        chat_ctx: agents_llm.ChatContext,
        tools: list | None = None,
        conn_options=None,
        parallel_tool_calls: bool | None = None,
        tool_choice=None,
        extra_kwargs: dict | None = None,
    ) -> "N8NStream":
        return N8NStream(
            llm=self,
            chat_ctx=chat_ctx,
            tools=tools or [],
            conn_options=conn_options,
        )


class N8NStream(agents_llm.LLMStream):
    """Stream de una sola respuesta devuelta por n8n."""

    def __init__(self, llm: N8NLLM, chat_ctx, tools, conn_options):
        super().__init__(
            llm, chat_ctx=chat_ctx, tools=tools, conn_options=conn_options
        )
        self._n8n_llm = llm

    async def _run(self):
        # Extrae el último mensaje del usuario
        text = ""
        if self._chat_ctx and self._chat_ctx.items:
            last = self._chat_ctx.items[-1]
            text = getattr(last, "text_content", "") or str(
                getattr(last, "content", "")
            )

        # Metadata útil (session id = nombre de la room)
        session_id = os.environ.get("LIVEKIT_ROOM_NAME", "default")

        response_text = "Disculpa, no pude procesarlo. ¿Puedes repetirlo?"
        try:
            session = await self._n8n_llm._get_session()
            async with session.post(
                self._n8n_llm._webhook_url,
                json={
                    "text": text,
                    "session_id": session_id,
                    "user_id": "livekit",
                },
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    response_text = (
                        data.get("response")
                        or data.get("text")
                        or data.get("output")
                        or response_text
                    )
                else:
                    logger.warning(
                        "n8n respondió %s: %s", resp.status, await resp.text()
                    )
        except Exception as e:
            logger.exception("Error llamando a n8n: %s", e)

        # Emite el texto como un único chunk
        chunk = agents_llm.ChatChunk(
            id="n8n-response",
            delta=agents_llm.ChoiceDelta(role="assistant", content=response_text),
        )
        self._event_ch.send_nowait(chunk)


# ─── Entrypoint del Worker ────────────────────────────────────
async def entrypoint(ctx: JobContext):
    logger.info("Conectando a la sala %s", ctx.room.name)
    await ctx.connect()

    # Exporta el nombre de la sala para usarlo como session_id
    os.environ["LIVEKIT_ROOM_NAME"] = ctx.room.name

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=openai.STT(
            model="Systran/faster-whisper-small",
            base_url=WHISPER_URL,
            language="es",
        ),
        llm=N8NLLM(N8N_WEBHOOK_URL, timeout=N8N_TIMEOUT),
        tts=cartesia.TTS(
            model="sonic-multilingual",
            voice=CARTESIA_VOICE_ID,
            language="es",
            api_key=CARTESIA_API_KEY or None,
        ),
        allow_interruptions=True,
    )

    agent = Agent(
        instructions=(
            "Eres un asistente espiritual y terapéutico de Esoter. "
            "Hablas siempre en español, con tono cálido y empático. "
            "Tus respuestas las genera un sistema RAG externo; "
            "limítate a transmitir la respuesta recibida."
        )
    )

    await session.start(agent=agent, room=ctx.room)

    # Saludo inicial
    await session.say("Hola, soy tu acompañante de Esoter. ¿En qué puedo ayudarte?")


# ─── Arranque del Worker ──────────────────────────────────────
if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="esoter-therapist",
        )
    )
