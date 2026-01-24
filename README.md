<p align="center">
  <img src="https://img.shields.io/badge/Web3-AI-blueviolet?style=for-the-badge&logo=ethereum&logoColor=white" alt="Web3 AI" />
  <img src="https://img.shields.io/badge/Monad-Testnet-orange?style=for-the-badge" alt="Monad" />
  <img src="https://img.shields.io/badge/Django-5.1-green?style=for-the-badge&logo=django" alt="Django" />
  <img src="https://img.shields.io/badge/x402-Protocol-ff69b4?style=for-the-badge" alt="x402" />
</p>

<h1 align="center">🤖 Web3.AI - Agent Economy Platform</h1>

<p align="center">
  <strong>Pay-Per-Use AI Agents powered by Blockchain Micro-payments</strong>
</p>

<p align="center">
  <a href="https://web3-ai-wg4j.onrender.com">🌐 Live Demo</a> •
  <a href="#-features">Features</a> •
  <a href="#-x402-protocol">x402 Protocol</a> •
  <a href="#-ai-agents">AI Agents</a> •
  <a href="#-getting-started">Getting Started</a>
</p>

---

## 🎯 What is Web3.AI?

**Web3.AI** is a next-generation platform that bridges **Decentralized Finance (DeFi)** and **Artificial Intelligence**. Instead of expensive monthly subscriptions, users pay **micro-amounts** (fractions of a cent) per AI task using cryptocurrency.

> 💡 **Think of it as:** Pay-per-query GPT, but on blockchain!

### 🔥 Why This Matters

| Traditional AI | Web3.AI |
|----------------|---------|
| $20/month subscription | Pay only for what you use |
| Credit card required | Crypto wallet (MetaMask) |
| Centralized billing | Decentralized payments |
| All or nothing | Micro-transactions |

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🔐 Web3 Authentication
- **No passwords, no emails**
- Login with MetaMask wallet
- Wallet address = Your identity

</td>
<td width="50%">

### 💸 Pay-Per-Use Model
- Micro-payments in MON tokens
- As low as **0.0001 MON** per query
- No monthly commitments

</td>
</tr>
<tr>
<td width="50%">

### ⚡ x402 Protocol
- HTTP 402 "Payment Required"
- Automatic payment flow
- Industry-standard approach

</td>
<td width="50%">

### 🧠 4 AI Agents
- GitHub Repository Analyzer
- Voice Intelligence (Audio→Text)
- CompeteScan (Competitor Analysis)
- Web Scraper

</td>
</tr>
</table>

---

## 🚀 x402 Protocol

### The Core Innovation

**x402** implements the HTTP 402 status code that was reserved for "Payment Required" since 1999 but never widely used—until now!

```
┌─────────────────────────────────────────────────────────────────────┐
│                        x402 PAYMENT FLOW                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   👤 User                                    🖥️ Server               │
│                                                                     │
│   1. Request AI Service ───────────────────►                        │
│                                                                     │
│   ◄─────────────────────────────────────── 2. HTTP 402 + Price Info │
│                                                                     │
│   3. MetaMask Opens                                                 │
│      User Approves Payment                                          │
│                                                                     │
│   4. Retry with Payment Proof ─────────────►                        │
│                                                                     │
│   ◄─────────────────────────────────────── 5. HTTP 200 + AI Result  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Response Format
```json
{
  "message": "Payment Required: GitHub Analysis Agent",
  "paymentRequirements": {
    "amount": "0.0005",
    "asset": "MON",
    "chain": "Monad Testnet",
    "chainId": "10143",
    "payTo": "0x9497...23B",
    "description": "GitHub Analysis Agent"
  }
}
```

---

## 🤖 AI Agents

| Agent | Endpoint | Price | What it Does |
|-------|----------|-------|--------------|
| 🔍 **Web Scraper** | `/api/x402/scraper/` | 0.0001 MON | Extracts content from any website |
| 📦 **GitHub Architect** | `/api/x402/github/` | 0.0005 MON | Analyzes repos: architecture, issues, PRs |
| 📊 **CompeteScan AI** | `/api/x402/competescan/` | 0.0010 MON | Competitor analysis with SWOT |
| 🎤 **Voice Intelligence** | `/api/x402/audio/` | 0.0011 MON | Audio transcription + meeting notes |

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| Django 5.1 | Web Framework |
| Python 3.11+ | Programming Language |
| web3.py | Blockchain Interactions |
| Google Gemini | AI Analysis Engine |
| ElevenLabs | Speech-to-Text |

### Frontend
| Technology | Purpose |
|------------|---------|
| Django Templates | Server-side Rendering |
| Vanilla JavaScript | Interactivity |
| ethers.js | Wallet Integration |
| TailwindCSS | Styling |

### Blockchain
| Property | Value |
|----------|-------|
| Network | Monad Testnet |
| Chain ID | 10143 |
| RPC | `https://testnet-rpc.monad.xyz` |
| Currency | MON |

---

## 📁 Project Structure

```
web3_ai/
├── 📂 agents/               # AI Agents App
│   ├── views.py             # 🔥 x402 endpoints & AI logic
│   ├── urls.py              # API routing
│   ├── models.py            # AnalysisTransaction model
│   └── scraper.py           # Web scraping utility
│
├── 📂 wallet/               # Authentication App
│   ├── views.py             # Wallet login/logout
│   └── models.py            # WalletUser model
│
├── 📂 payment/              # PayLink System
│   ├── views.py             # QR code generation
│   └── models.py            # Payment models
│
├── 📂 templates/
│   └── dashboard.html       # 🔥 Main UI + x402 JavaScript
│
├── 📂 static/               # CSS, JS, images
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
├── Procfile                 # Render deployment
└── README.md                # This file
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- MetaMask wallet
- MON tokens (Monad Testnet faucet)

### 1. Clone Repository
```bash
git clone https://github.com/Vanshhsoni/lnmiit_jeetenge_hackathon.git
cd lnmiit_jeetenge_hackathon/web3_ai
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Setup
```bash
cp .env.example .env
# Edit .env and add your API keys
```

### 5. Run Migrations
```bash
python manage.py migrate
```

### 6. Start Server
```bash
python manage.py runserver
```

### 7. Visit
```
http://localhost:8000
```

---

## ⚙️ Environment Variables

Create a `.env` file in the root directory:

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=*

# AI Services
GEMINI_API_KEY=your-gemini-api-key
ELEVENLABS_API_KEY=your-elevenlabs-api-key
```

> ⚠️ **Never commit your `.env` file to Git!**

---

## 🌐 Deployment (Render)

This project is configured for easy Render deployment:

1. Connect your GitHub repo to Render
2. Set environment variables in Render dashboard
3. Deploy!

**Build Command:** `./build.sh`  
**Start Command:** `gunicorn web3_ai.wsgi:application`

---

## 🗺️ Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Basic AI Agents | ✅ Complete |
| 2 | x402 Protocol | ✅ Complete |
| 3 | Smart Contract Integration | 🔄 Planned |
| 4 | Multi-chain Support | 🔄 Planned |
| 5 | Agent-to-Agent Payments | 🔄 Planned |

---

## 🔒 Security

- ✅ CSRF Protection
- ✅ Wallet-based Auth (no passwords)
- ✅ x402 Standard Headers
- ✅ Input Validation
- ✅ Rate Limiting Ready

---

## 📖 API Quick Reference

### Using x402 (Backend)
```python
@login_required
@require_POST
@x402_payment_required(
    required_amount=0.0001, 
    asset="MON", 
    description="My Agent"
)
def my_agent(request):
    # Runs only after payment verified
    return JsonResponse({"result": "success"})
```

### Using x402 (Frontend)
```javascript
const res = await window.x402Fetch('/api/x402/my-agent/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: 'value' })
});
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📄 License

This project is built for **LNMIIT Jeetenge Hackathon**.

---

<p align="center">
  <strong>🌐 Live at: <a href="https://web3-ai-wg4j.onrender.com">https://web3-ai-wg4j.onrender.com</a></strong>
</p>

<p align="center">
  Built with ❤️ for LNMIIT Jeetenge Hackathon
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-Python-blue?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/Powered%20by-Monad-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/AI-Gemini%202.5-purple?style=flat-square" />
</p>
