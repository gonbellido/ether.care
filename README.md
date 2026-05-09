# 🧠 ether.care — Multi-Agent Omnichannel AI System

**Autonomous AI system for WhatsApp, RAG, LiveKit STT/TTS, and CrewAI-based multi-agent orchestration.**

[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://docs.docker.com/compose/)
[![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-orange)](https://crewai.com)
[![LiveKit](https://img.shields.io/badge/LiveKit-Real--time-green)](https://livekit.io)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-Cloud%20API-brightgreen)](https://developers.facebook.com/docs/whatsapp)

## 🎯 What It Does

ether.care is a production-grade multi-agent system that:

- 📱 **Manages WhatsApp & omnichannel** — Receives and responds to messages from WhatsApp, social media, and other channels from a single system
- 🧑‍💼 **Profiles people** — Automatically builds a profile for each person based on their interactions
- 💬 **Advises & responds** — Generates personalized responses and activities using a specialized knowledge base
- 🧠 **Remembers context** — Maintains history and context for every person across all channels

## 🤖 Agents

| Agent | Role | Tech |
|-------|------|------|
| **Orchestrator** | Central coordinator — decides which agents to activate per message | CrewAI |
| **Profiler** | Extracts user info and updates their profile | LLM + PostgreSQL |
| **Advisor** | Generates responses, advice and activities based on profile + knowledge | RAG + LLM |
| **Channel Adapters** | Normalize messages from each channel to internal format | WhatsApp API + Webhooks |

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Orchestration** | CrewAI (multi-agent framework) |
| **LLM** | Claude (Anthropic) |
| **Voice** | LiveKit STT/TTS (real-time speech-to-text / text-to-speech) |
| **RAG** | PostgreSQL + pgvector (vector search) |
| **Messaging** | WhatsApp Cloud API |
| **Infrastructure** | Docker Compose, PostgreSQL, Redis |
| **Config** | YAML-driven agent configuration |

## 📁 Architecture

```
ether.care/
├── crewai/          # Multi-agent definitions (orchestrator, profiler, advisor)
├── livekit/         # LiveKit server + agent config for real-time voice
├── livekit-agent/   # Custom LiveKit agent (STT/TTS integration)
├── kokoro/          # Kokoro TTS engine
├── postgres/        # Database schemas + pgvector config
├── config/          # Agent YAML configurations
├── diagnostico/     # System health checks + diagnostics
└── docker-compose.yml
```

## 🚀 Quick Start

```bash
docker compose up -d
```

Requires: Docker, API keys for Anthropic, WhatsApp Cloud API, and LiveKit.

## 👤 Author

**Gonzalo Bellido** — AI Automation Engineer & Applied AI Systems Builder

- [LinkedIn](https://www.linkedin.com/in/gonzalo-bellido/)
- [Email](mailto:gonbellido@protonmail.com)
- [WooSale.pro](https://woosales.pro)
