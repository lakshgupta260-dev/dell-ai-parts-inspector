# Dell AI Parts Inspector - Presentation Day Run Guide

Follow these exact steps to get the entire project running perfectly on the presentation device provided by Dell.

## ⚠️ VERY IMPORTANT PRE-REQUISITE
Before the presentation, you **must** securely transfer your `backend/.env` file from your personal laptop to a USB drive or secure cloud storage. This file contains all your secret API keys (Vapi, Meta, OpenAI) and is ignored by GitHub for security reasons.

---

## 1. Get the Code
Open a terminal (PowerShell or Command Prompt) on the presentation device and clone your repository:
```bash
git clone https://github.com/lakshgupta260-dev/dell-ai-parts-inspector.git
cd dell-ai-parts-inspector
```

## 2. Start the Python Backend
Open a new terminal window inside the `dell-ai-parts-inspector` folder:
```bash
cd backend

# Create a virtual environment
python -m venv venv

# Activate it (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**[CRITICAL STEP]**: Now, take that `backend/.env` file you saved on your USB drive and copy it into the `backend` folder on the new laptop.

```bash
# Start the server
python -m uvicorn app.main:app --reload
```
*(Leave this terminal running in the background)*

## 3. Start the React Frontend
Open a **second** terminal window inside the `dell-ai-parts-inspector` folder:
```bash
cd dell-frontend

# Install node modules
npm install

# Start the frontend UI
npm run dev
```
*(Leave this terminal running in the background)*

## 4. Start ngrok (For WhatsApp & Vapi Voice Calls)
Since you are on a new laptop, ngrok will generate a brand new public URL. We need this so Meta knows how to reach the new laptop.

Open a **third** terminal window:
```bash
ngrok http 8000
```
Copy the new Forwarding URL (e.g., `https://brand-new-url.ngrok-free.app`).

## 5. Update Meta Webhook
Because your ngrok URL changed, you must tell Meta the new URL so the WhatsApp buttons work.
1. Go to your **[Meta App Dashboard](https://developers.facebook.com/apps)**.
2. Click **WhatsApp** -> **Configuration** in the left menu.
3. Under Webhooks, click **Edit**.
4. Paste your NEW ngrok URL followed by `/api/v1/webhook/whatsapp`. 
   *(Example: `https://brand-new-url.ngrok-free.app/api/v1/webhook/whatsapp`)*
5. The Verify Token is still `dell_secret_token_123`.
6. Click **Verify and Save**.

---

## 🎉 You're Ready to Present!
- Open your browser to `http://localhost:5173` to show the UI.
- Take a photo of a part, let the AI inspect it, and click "Send to WhatsApp".
- Open your phone, click "Call AI Assistant" and watch the judges' jaws drop when the phone rings!
