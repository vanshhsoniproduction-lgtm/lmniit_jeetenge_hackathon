# 📋 Product Requirements Document (PRD): Web3 AI Agent Platform

**Project Name:** Web3.AI - Autonomous Agent Platform  
**Version:** 2.0 (x402 Protocol Update)  
**Status:** ✅ Complete  
**Last Updated:** January 24, 2026

---

## 📌 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [x402 Protocol (HIGHLIGHT)](#2-x402-protocol-highlight)
3. [Technology Stack](#3-technology-stack)
4. [Code Locations](#4-code-locations)
5. [System Architecture](#5-system-architecture)
6. [AI Agents](#6-ai-agents)
7. [Workflows](#7-workflows)
8. [Frontend & Backend Roles](#8-frontend--backend-roles)
9. [Security](#9-security)
10. [Future Roadmap](#10-future-roadmap)

---

## 1. Executive Summary

This project is a **Web3-native AI Agent Platform**. It bridges decentralized finance (DeFi) and artificial intelligence by offering **pay-per-use AI services** via the **Monad Testnet**.

### 🎯 Key Features

| Feature | Description |
|---------|-------------|
| **Web3 Auth** | Login via MetaMask wallet (no email/password) |
| **Pay-Per-Use** | Micro-payments instead of subscriptions |
| **x402 Protocol** | HTTP 402 Payment Required standard |
| **5 AI Agents** | GitHub, Voice, CompeteScan, Scraper, Portfolio |
| **Monad Blockchain** | Fast & cheap transactions |

---

## 2. x402 Protocol (HIGHLIGHT)

### 🚨 **THIS IS THE MAIN INNOVATION OF THIS PROJECT!**

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                          x402 PROTOCOL                                        ║
║                  HTTP 402 "Payment Required" Standard                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### What is x402?

**x402** is a modern implementation of the HTTP 402 status code that enables **pay-per-API-call** using cryptocurrency. It's the foundation of the **Agent Economy** - where AI agents can autonomously pay for services.

### How it Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        x402 PROTOCOL FLOW                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   FRONTEND                          BACKEND                                 │
│   ────────                          ───────                                 │
│                                                                             │
│   1. fetch('/api/x402/github/')  ─────────────► Check x-payment header     │
│      (no x-payment header)                      │                          │
│                                                 ▼                          │
│                                         Header missing?                    │
│                                                 │                          │
│   ◄─────────────────────────────────────────── YES                         │
│   HTTP 402 Payment Required                     │                          │
│   + Payment Requirements JSON                   │                          │
│                                                 │                          │
│   2. Parse payment requirements                 │                          │
│      Amount: 0.0005 MON                         │                          │
│      Chain: Monad Testnet                       │                          │
│      Recipient: 0x9497...                       │                          │
│                                                 │                          │
│   3. Open MetaMask                              │                          │
│      User signs transaction                     │                          │
│                                                 │                          │
│   4. Wait for confirmation                      │                          │
│                                                 │                          │
│   5. Retry with x-payment header ────────────► Check x-payment header      │
│      (x-payment: 0x1234...)                     │                          │
│                                                 ▼                          │
│                                         Header present?                    │
│                                                 │                          │
│   ◄─────────────────────────────────────────── YES                         │
│   HTTP 200 + AI Analysis Data                   │                          │
│                                           Process request!                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### x402 Response Format

When payment is required, the server returns:

```json
{
  "message": "Payment Required: GitHub Analysis Agent",
  "paymentRequirements": {
    "amount": "0.0005",
    "asset": "MON",
    "chain": "Monad Testnet",
    "chainId": "10143",
    "payTo": "0x9497FE4B4ECA41229b9337abAEbCC91eCc7be23B",
    "description": "GitHub Analysis Agent"
  }
}
```

**Headers returned:**
- `x-evm-chain-id: 10143`
- `x-payment-address: 0x9497...`
- `x-price-currency: MON`
- `x-price-amount: 0.0005`

### x402 Advantages

| Old Method | x402 Method |
|------------|-------------|
| User pays first, then calls API | API tells user "pay me first" |
| Manual tx_hash passing | Automatic payment flow |
| User manages payment | SDK handles everything |
| Tight coupling | Loose coupling (standard protocol) |

---

## 3. Technology Stack

### Backend

| Technology | Purpose |
|------------|---------|
| Django 5.1.6 | Web framework |
| Python 3.11+ | Programming language |
| SQLite | Database (dev) |
| web3.py | Blockchain interaction |
| Google Gemini 2.5 | AI analysis |
| ElevenLabs API | Speech-to-text |
| CoinGecko API | Real-time Market Data |

### Frontend

| Technology | Purpose |
|------------|---------|
| Django Templates | Server-side rendering |
| Vanilla JavaScript | Interactivity |
| TailwindCSS Classes | Styling |
| ethers.js | Wallet interaction |
| Thirdweb SDK | x402 payment handling |

### Blockchain

| Property | Value |
|----------|-------|
| Network | Monad Testnet |
| Chain ID | 10143 |
| RPC URL | https://testnet-rpc.monad.xyz |
| Currency | MON |

---

## 4. Code Locations

### 📁 Critical File Locations

```
web3_ai/
├── agents/                          # AI Agents App
│   ├── views.py                     # 🔥 MAIN BACKEND LOGIC (x402 decorators, API handlers)
│   ├── urls.py                      # API URL routing (/api/x402/...)
│   ├── models.py                    # Database models (AnalysisTransaction)
│   └── scraper.py                   # Website scraping utility
│
├── templates/
│   └── dashboard.html               # 🔥 MAIN FRONTEND (x402 JavaScript module)
│
├── wallet/                          # Authentication App
│   ├── views.py                     # Wallet login/logout
│   └── models.py                    # WalletUser model
│
├── payment/                         # PayLink System
│   ├── views.py                     # QR code generation
│   └── models.py                    # PaymentRequest, PaymentTransaction
│
└── PRD.md                           # This document
```

### 🎯 x402 Specific Locations

| Component | File | Line Numbers |
|-----------|------|--------------|
| x402 Decorator | `agents/views.py` | Lines 133-201 |
| x402 Scraper Endpoint | `agents/views.py` | Lines 683-770 |
| x402 GitHub Endpoint | `agents/views.py` | Lines 785-850 |
| x402 CompeteScan Endpoint | `agents/views.py` | Lines 860-930 |
| x402 Audio Endpoint | `agents/views.py` | Lines 940-1005 |
| x402 Portfolio Endpoint | `agents/views.py` | Lines 1000+ |
| x402Fetch (Frontend) | `templates/dashboard.html` | Lines 1193-1280 |
| x402FetchFormData | `templates/dashboard.html` | Lines 1290-1360 |
| x402 URL Routes | `agents/urls.py` | Lines 98-135 |

---

## 5. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SYSTEM ARCHITECTURE                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Browser    │     │    Django    │     │   External   │     │  Blockchain  │
│  (Frontend)  │     │  (Backend)   │     │    APIs      │     │   (Monad)    │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │
       │  1. Click Agent    │                    │                    │
       ├───────────────────►│                    │                    │
       │                    │                    │                    │
       │  2. HTTP 402       │                    │                    │
       │◄───────────────────┤                    │                    │
       │                    │                    │                    │
       │  3. MetaMask Tx    │                    │                    │
       ├────────────────────┼────────────────────┼───────────────────►│
       │                    │                    │                    │
       │  4. Tx Confirmed   │                    │                    │
       │◄────────────────────────────────────────────────────────────┤
       │                    │                    │                    │
       │  5. Retry + Header │                    │                    │
       ├───────────────────►│                    │                    │
       │                    │  6. Call AI API   │                    │
       │                    ├───────────────────►│                    │
       │                    │                    │                    │
       │                    │  7. AI Response   │                    │
       │                    │◄───────────────────┤                    │
       │                    │                    │                    │
       │  8. Final Result   │                    │                    │
       │◄───────────────────┤                    │                    │
       │                    │                    │                    │
```

---

## 6. AI Agents

### 🤖 Available Agents

| Agent | Endpoint | Price | Description |
|-------|----------|-------|-------------|
| **Web Scraper** | `/api/x402/scraper/` | 0.0001 MON | Scrapes website content |
| **GitHub Architect** | `/api/x402/github/` | 0.0005 MON | Repository analysis |
| **CompeteScan AI** | `/api/x402/competescan/` | 0.0010 MON | Competitor analysis |
| **Voice Intelligence** | `/api/x402/audio/` | 0.0011 MON | Audio transcription |
| **Smart Portfolio Architect** | `/api/x402/finance/` | 0.0015 MON | AI Crypto Investment Advisor |

### Agent Details

#### 1. Web Scraper (x402)
- **Input:** Website URL
- **Output:** Scraped text content
- **File:** `agents/views.py` → `run_scraper_x402()`

#### 2. GitHub Architect (x402)
- **Input:** GitHub repository URL, analysis type
- **Output:** HTML formatted analysis
- **Types:** summary, architecture, issues, pr_review
- **File:** `agents/views.py` → `run_github_x402()`

#### 3. CompeteScan AI (x402)
- **Input:** Competitor website URL
- **Output:** JSON with overview, pricing, SWOT, insights
- **File:** `agents/views.py` → `run_competescan_x402()`

#### 4. Voice Intelligence (x402)
- **Input:** Audio file (MP3/WAV)
- **Output:** Transcript, minutes, todos, deadlines
- **File:** `agents/views.py` → `run_audio_x402()`

#### 5. Smart Portfolio Architect (x402)
- **Input:** User portfolio / Investment goals
- **Output:** Risk analysis, rebalancing advice, market sentiment
- **File:** `agents/views.py` → `run_finance_x402()`

---

## 7. Workflows

### A. User Onboarding
```
1. User visits homepage
2. Clicks "Connect Wallet"
3. MetaMask popup opens
4. User approves connection
5. Backend creates/fetches WalletUser
6. User redirected to Dashboard
```

### B. Using an AI Agent (x402 Flow)
```
1. User selects agent (e.g., GitHub)
2. User enters input (e.g., repo URL)
3. User clicks "Execute"
4. Frontend sends POST request
5. Backend returns HTTP 402
6. Frontend opens MetaMask
7. User approves payment
8. Transaction confirms
9. Frontend retries with x-payment header
10. Backend processes request
11. AI generates response
12. Results displayed to user
```

### C. Payment Verification
```
1. x-payment header contains tx_hash
2. Backend extracts tx_hash
3. (Optional) Verify on blockchain
4. Save to AnalysisTransaction model
5. Process request
```

---

## 8. Frontend & Backend Roles

### 🖥️ Frontend Role (dashboard.html)

| Responsibility | Implementation |
|----------------|----------------|
| User Interface | HTML/CSS with premium design |
| View Switching | JavaScript `switchView()` function |
| x402 Detection | `x402Fetch()` checks for 402 status |
| Wallet Interaction | ethers.js + MetaMask |
| Payment Handling | Automatic via x402Fetch |
| Results Display | Dynamic HTML injection |

**Key Functions:**
- `x402Fetch(url, options)` - Main payment wrapper
- `x402FetchFormData(url, formData)` - File upload handler
- `runGithubAgent()` - GitHub API caller
- `runAudioAgent()` - Audio API caller
- `runCompeteScan()` - CompeteScan API caller
- `runScraperX402()` - Scraper API caller

### ⚙️ Backend Role (views.py)

| Responsibility | Implementation |
|----------------|----------------|
| x402 Protocol | `@x402_payment_required` decorator |
| Payment Validation | Check x-payment header |
| AI API Calls | Google Gemini, ElevenLabs |
| Data Storage | AnalysisTransaction model |
| Scraping | BeautifulSoup scraper |
| Response Formatting | JsonResponse |

**Key Functions:**
- `x402_payment_required()` - Decorator for payment
- `run_scraper_x402()` - Scraper endpoint
- `run_github_x402()` - GitHub endpoint
- `run_competescan_x402()` - CompeteScan endpoint
- `run_audio_x402()` - Audio endpoint
- `verify_payment()` - Transaction verification

---

## 9. Security

### Security Measures

| Measure | Description |
|---------|-------------|
| CSRF Protection | Django CSRF tokens |
| x402 Headers | Standard payment headers |
| Login Required | `@login_required` decorator |
| Wallet Auth | No passwords stored |
| Input Validation | URL/file validation |

### Recommendations for Production

1. Move API keys to `.env` file
2. Use PostgreSQL instead of SQLite
3. Add rate limiting
4. Implement tx verification on blockchain
5. Add HTTPS enforcement

---

## 10. Future Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| Phase 1 | Basic AI Agents | ✅ Complete |
| Phase 2 | x402 Protocol | ✅ Complete |
| Phase 3 | Smart Contract Integration | 🔄 Planned |
| Phase 4 | Multi-chain Support | 🔄 Planned |
| Phase 5 | Agent-to-Agent Payments | 🔄 Planned |

---

## 📝 Quick Reference

### x402 Decorator Usage

```python
@login_required
@require_POST
@x402_payment_required(required_amount=0.0001, asset="MON", description="My Agent")
def my_agent(request):
    # This code only runs if payment is verified
    return JsonResponse({"result": "success"})
```

### x402 Frontend Usage

```javascript
const res = await window.x402Fetch('/api/x402/my-agent/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: 'value' })
});
```

---

**🎉 Project Complete!**

*Built with ❤️ by Web3.AI Team*
