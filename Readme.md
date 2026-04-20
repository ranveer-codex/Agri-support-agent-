# 🌾 Agri Support Agent

An AI-powered agricultural assistant chatbot that helps farmers and agri-enthusiasts get instant, intelligent answers to questions about crops, pests, soil health, fertilizers, and farming practices.

> **Live Demo:** [agri-support-agent.vercel.app](https://agri-support-agent.vercel.app)

---

## 🚀 Features

- 💬 **Real-time AI Chat** — Conversational interface powered by Anthropic's Claude API
- ⚡ **WebSocket Support** — Low-latency, streaming responses for a smooth chat experience
- 🌱 **Agriculture-Focused** — Specialized context for crop advisory, pest identification, soil guidance, and more
- 📱 **Responsive UI** — Clean, mobile-friendly React frontend
- 🔌 **Decoupled Architecture** — Separate frontend (Vercel) and backend (Railway) deployments

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React.js, Vite, CSS |
| Backend | FastAPI (Python) |
| AI Model | Anthropic Claude (via Anthropic SDK) |
| Real-time | WebSockets |
| Frontend Hosting | Vercel |
| Backend Hosting | Railway |

---

## 📁 Project Structure

```
Agri-support-agent-/
├── frontend/               # React + Vite frontend
│   ├── src/
│   │   ├── components/     # UI components
│   │   └── App.jsx         # Root component
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
└── backend/                # FastAPI backend
    ├── main.py             # Entry point, API routes, WebSocket handler
    └── requirements.txt    # Python dependencies
```

---

## ⚙️ Getting Started (Local Setup)

### Prerequisites
- Node.js v18+
- Python 3.10+
- Anthropic API Key

### 1. Clone the repository

```bash
git clone https://github.com/ranveer-codex/Agri-support-agent-.git
cd Agri-support-agent-
```

### 2. Setup Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` folder:

```env
ANTHROPIC_API_KEY=your_api_key_here
```

Run the backend:

```bash
uvicorn main:app --reload
```

### 3. Setup Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be running at `http://localhost:5173`

---

## 🔑 Environment Variables

| Variable | Location | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | `backend/.env` | Your Anthropic API key |
| `VITE_BACKEND_URL` | `frontend/.env` | Backend WebSocket/API URL |

> ⚠️ Never commit `.env` files. They are listed in `.gitignore`.

---

## 🌐 Deployment

| Service | Platform | Status |
|---------|----------|--------|
| Frontend | Vercel | ✅ Live |
| Backend | Railway | 🔧 In Progress |

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## 👤 Author

**Ranveer**
- GitHub: [@ranveer-codex](https://github.com/ranveer-codex)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
