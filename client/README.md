# G Force Voice Agent Client

React and TypeScript browser interface for the G Force Voice Agent. It supports WebRTC and WebSocket sessions, microphone and typed input, transcripts, voice controls, service configuration, and latency metrics.

The client is based on the browser interface from NVIDIA [Nemotron Voice Agent](https://github.com/NVIDIA-AI-Blueprints/nemotron-voice-agent) and uses the Pipecat Client SDK.

## Development

```bash
npm ci
npm run lint
npm run build
npm run dev
```

The Vite development server runs on `http://localhost:5173` and requires the Python backend APIs. For complete testing, use the root Docker Compose deployment and open `https://localhost:7860/`.
