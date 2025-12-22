# Deploying VoiceBot to Vercel

This guide explains how to deploy the VoiceBot application to Vercel.

## Prerequisites

1.  **Vercel Account**: Sign up at [vercel.com](https://vercel.com).
2.  **Vercel CLI** (Optional): `npm i -g vercel`

## Configuration

We have prepared the following configuration files:
- `vercel.json`: Specifies the entry point (`src/api/main.py`).
- `requirements.txt`: Minimal dependencies for deployment.
- `.vercelignore`: Excludes unnecessary files.

## Steps to Deploy

### 1. Push to GitHub
Push your code to a GitHub repository.

### 2. Import Project in Vercel
1.  Go to Vercel Dashboard -> **Add New...** -> **Project**.
2.  Select your GitHub repository.
3.  Vercel will auto-detect the configuration from `vercel.json`.

### 3. Configure Environment Variables
In the "Environment Variables" section during import, add the following:

- `GROQ_API_KEY`: Your Groq API key.
- `GOOGLE_API_KEY`: Your Google Gemini API key (optional).
- `GUARDRAILS_ENABLED`: `true` or `false`.
- `LOG_LEVEL`: `INFO`

### 4. Deploy
Click **Deploy**.

## ⚠️ Important Limitations

### Function Size Limit (250MB)
This application uses `sentence-transformers` and `chromadb` for the RAG system. These libraries rely on **PyTorch**, which is very large (>700MB). 
**The deployment will likely FAIL** with a "Function size exceeded" error on the free tier.

**Solution:**
If the deployment fails due to size, you must switch to a lightweight embedding model or an API-based embedding provider (like OpenAI or Google Gemini Embeddings) and remove `sentence-transformers` from `requirements.txt`.

### File Persistence
Vercel Serverless Functions are **read-only** (except `/tmp`).
- You **cannot upload new documents** via the API in production.
- The existing documents in `data/vectordb` will be available (read-only) because we committed them to the repo.

## Alternative Deployment (Recommended)
For full functionality (uploads, persistent DB, no size limits), deploy to **Render**, **Railway**, or **Fly.io** using the included `Dockerfile`.

### Deploying to Render
1.  Create a **Web Service** on Render.
2.  Connect your repo.
3.  Runtime: **Docker**.
4.  Add Environment Variables.
5.  Deploy.
