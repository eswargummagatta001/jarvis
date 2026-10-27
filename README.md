# ⚡ J.A.R.V.I.S — AI Personal Executive Assistant

> A real voice-controlled AI executive assistant with instant offline deterministic actions, Groq Cloud LLM intelligence, real-time live market updates, and a 3D holographic HUD interface.

---

## 🌟 Key Features

- **🎙️ Real-Time Voice Assistant**: Listens continuously via microphone with high-accuracy speech recognition.
- **🌐 3D Holographic Workplace HUD**: Interactive browser interface on `http://localhost:8080` with cyber reactor core, animated globe, voice oscilloscope, and telemetry chat.
- **⚡ Deterministic Voice Actions**:
  - **YouTube**: Open homepage or search/play videos directly (*"Play lofi on YouTube"*).
  - **WhatsApp**: Open WhatsApp Web or draft messages (*"Send WhatsApp message to Alex"*).
  - **App Launch**: Launch any macOS / local applications (*"Open Chrome"*, *"Open VS Code"*).
  - **Live Market Intelligence**: Real-time Nifty, Sensex, Nvidia, Bitcoin quotes and Buy/Hold/Sell signals.
  - **Calendar & Reminders**: Schedule events and set quick voice timers.
  - **Volume & Audio Control**: System volume up/down, mute audio.
  - **Weather & News**: Instant live weather reports and top headlines.
  - **Email Briefings**: Priority unread email summaries.
- **🧠 Groq AI Cloud Brain**: Powered by high-speed Groq inference (`openai/gpt-oss-120b`, `llama-3.3`) for conversational queries.
- **🛡️ Resilient Hybrid Failover**: Automatically detects rate limits and smoothly falls back to local processing without crashing.

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/eswargummagatta001/jarvis.git
cd jarvis
```

### 2. Set up Python Environment (Python 3.12 recommended)
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure API Key
Copy the example environment file and add your Groq API key:
```bash
cp .env.example .env
```
Edit `.env` and set:
```env
GROQ_API_KEY=your_groq_api_key_here
```
*(Or save it to `~/.openjarvis/free.key`)*

### 4. Run the Integrated Assistant & Workplace Server
```bash
python jarvis_server.py
```
Open **[http://localhost:8080](http://localhost:8080)** in your browser to view the live Holographic Workplace HUD! Speak into your microphone or send commands over HTTP.

---

## 🗣️ Example Voice Commands

| Category | Example Voice Command |
|---|---|
| **App Launch** | *"Jarvis, open Google Chrome"* / *"Open VS Code"* |
| **YouTube** | *"Play lofi music on YouTube"* / *"Open YouTube"* |
| **Messaging** | *"Open WhatsApp"* / *"Message John on WhatsApp saying I'll be there soon"* |
| **Market** | *"Stock market update"* / *"Should I buy Bitcoin?"* |
| **Utility** | *"What's the weather in London?"* / *"What time is it?"* |
| **Reminders** | *"Remind me in 5 minutes to take a break"* |
| **System** | *"Volume up"*, *"Volume down"*, *"Mute"* |
| **AI Brain** | Ask any general question or coding problem! |

---

## 🛠️ Project Structure

```
├── jarvis_server.py            # Integrated HTTP Server & Background Voice Listener
├── Jarvis_Setup_Package/
│   ├── jarvis_brain.py         # Cloud LLM reasoning & rate-limit failover engine
│   ├── jarvis_actions.py       # Instant local deterministic actions
│   ├── jarvis_market.py        # Real-time stock & crypto market analyzer
│   ├── jarvis_voice.py         # Dedicated voice loop script
│   └── jarvis_workplace.html   # Holographic Iron Man HUD UI
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
└── .gitignore                  # Git ignore rules
```

---

## 📄 License
MIT License. Built for seamless personal desktop automation.
