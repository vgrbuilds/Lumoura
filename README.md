## Overview

Lumoura is a full-stack research assistant that turns a user query into a structured, source-backed answer. The server now includes authenticated accounts, credit-based research usage, Razorpay subscriptions, and history tracking for research sessions and transactions. The core flow searches for relevant sources, scrapes the best pages, and synthesizes a final response with Gemini.

Full technical documentation lives in [`docs/`](D:/projects/Lumoura/docs/README.md).

## Features

1. Source-backed research responses

2. Web search plus page scraping for richer context

3. Gemini-powered answer synthesis

4. Structured API responses for client integration

5. Health check endpoint for deployment and monitoring

6. Clear fallback path when scraping is unavailable

7. Authenticated accounts, credit deduction, and subscription billing

## Tech Stack

1. Client application: React JS, Vite, AntD, Tailwind CSS

2. Server application: FastAPI, Pydantic, Uvicorn, Docker

3. Auth and security: JWT, password hashing

4. Agentic AI: LangChain, Gemini AI

5. External APIs and SDKs: Tavily, Razorpay, BeautifulSoup, Requests, lxml

6. Configuration: Python dotenv, environment variables, MongoDB Atlas

## Setup

1. Clone the repository

   ```powershell
   git clone https://github.com/vgrbuilds/Lumoura.git
   cd Lumoura
   ```

2. Set up the server environment

   ```powershell
   cd server
   uv sync
   ```

   Or run the full local stack with Docker:

   ```powershell
   docker compose up --build
   ```

3. Add the required server environment variables in `server/.env`

   ```env
   GOOGLE_API_KEY=your_google_api_key
   TAVILY_API_KEY=your_tavily_api_key
   MONGO_URI=your_mongodb_connection_string
   JWT_SECRET=your_long_random_jwt_secret
   RAZORPAY_TEST_KEY_ID=your_razorpay_test_key_id
   RAZORPAY_KEY_SECRET=your_razorpay_key_secret
   RAZORPAY_WEBHOOK_SECRET=your_razorpay_webhook_secret
   SUBSCRIPTION_PLAN_AMOUNT=99900
   SUBSCRIPTION_PLAN_CREDITS=300
   CORS_ORIGINS=http://localhost:5173
   CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
   CLOUDINARY_API_KEY=your_cloudinary_api_key
   CLOUDINARY_API_SECRET=your_cloudinary_api_secret
   ```

   You can start from `server/.env.example` and fill in the real values.

4. Start the server

   ```powershell
   uv run uvicorn src.main:app --reload
   ```

5. In a second terminal, start the client

   ```powershell
   cd client
   npm install
   npm run dev
   ```

6. Test the API

   ```powershell
   Invoke-RestMethod http://127.0.0.1:8000/health
   ```

   ```powershell
   Invoke-RestMethod -Method Post http://127.0.0.1:8000/research `
     -ContentType "application/json" `
     -Headers @{ Authorization = "Bearer YOUR_TOKEN_HERE" } `
     -Body '{"query":"What is the future of renewable energy?"}'
   ```

   With research controls:

   ```powershell
   Invoke-RestMethod -Method Post http://127.0.0.1:8000/research `
     -ContentType "application/json" `
     -Headers @{ Authorization = "Bearer YOUR_TOKEN_HERE" } `
     -Body '{
       "query":"What is the future of renewable energy?",
       "preferences":{
         "tone":"analytical",
         "creativity":3,
         "audience":"founders",
         "depth":"deep",
         "output_format":"report",
         "language":"English",
         "max_sources":5,
         "extra_context":"Focus on policy, cost, and adoption challenges.",
         "include_citations":true
       }
     }'
   ```

   Auth and account endpoints:

   ```powershell
   Invoke-RestMethod -Method Post http://127.0.0.1:8000/auth/register `
     -ContentType "application/json" `
     -Body '{"name":"Test User","email":"test@example.com","password":"Password123!"}'
   ```

   ```powershell
   Invoke-RestMethod -Method Get http://127.0.0.1:8000/auth/me `
     -Headers @{ Authorization = "Bearer YOUR_TOKEN_HERE" }
   ```

   Billing endpoints:

   ```powershell
   Invoke-RestMethod http://127.0.0.1:8000/billing/config
   ```

   ```powershell
   Invoke-RestMethod -Method Post http://127.0.0.1:8000/billing/subscriptions `
     -ContentType "application/json" `
     -Headers @{ Authorization = "Bearer YOUR_TOKEN_HERE" } `
     -Body '{"plan_code":"monthly"}'
   ```

   Account history endpoints:

   ```powershell
   Invoke-RestMethod -Method Get http://127.0.0.1:8000/account/overview `
     -Headers @{ Authorization = "Bearer YOUR_TOKEN_HERE" }
   ```

## Deployment

1. Deploy the server as a separate service

   Use a container host such as Render, Railway, Fly.io, or a VM. The server has a Dockerfile at `server/Dockerfile`, so you can deploy the container directly.

   For Render, point the service at `server/Dockerfile` and set the environment variables from the setup section.

2. Deploy the client as a static frontend

   Build the Vite app and host it on Vercel, Netlify, Cloudflare Pages, or similar:

   ```powershell
   npm run build
   ```

3. Point the client at the deployed API

   Update the client to call the hosted FastAPI URL instead of `localhost`.

4. Configure environment variables in production

   Add `GOOGLE_API_KEY`, `TAVILY_API_KEY`, `MONGO_URI`, `JWT_SECRET`, `RAZORPAY_TEST_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET` to the server host. If you change the subscription offer, update `SUBSCRIPTION_PLAN_AMOUNT` and `SUBSCRIPTION_PLAN_CREDITS` too.

5. Allow CORS for the deployed frontend

   The FastAPI app already enables CORS broadly, but in production you should restrict it to your actual frontend domain.

6. Recommended production layout

   - Frontend: Vercel or Netlify
   - Backend: Render, Railway, or Fly.io
   - Secrets: platform environment variables
   - Database: MongoDB Atlas, if you add research session storage
   - Container local dev: `docker compose up --build`

7. Simple deployment path

   If you want the fastest route, deploy the backend first, confirm `/health` works, then deploy the frontend and wire it to the backend URL.

8. If you are testing billing locally

   Use the Docker Compose stack or a MongoDB Atlas replica set so the credit and billing transactions can use MongoDB sessions safely.
