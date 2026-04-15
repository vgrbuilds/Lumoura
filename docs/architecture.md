# Architecture

## High-Level View

Lumoura uses a split architecture:

- `client/` for the React frontend
- `server/` for the FastAPI backend
- MongoDB for persistence
- Razorpay for subscriptions and webhook-driven billing events
- Cloudinary for storing research exports
- Tavily and Gemini for research generation

## Server Layers

The backend is organized into these layers:

1. API layer
   - FastAPI routers expose auth, account, research, and billing endpoints.

2. Core layer
   - Configuration, database access, auth helpers, and request identity resolution live here.

3. Service layer
   - Each service owns one business capability: users, credits, research sessions, exports, billing, Cloudinary, and synthesis.

4. Schema layer
   - Pydantic models define request and response contracts.

## Request Flow

1. The client sends a request to the FastAPI app.
2. The auth dependency validates the JWT and loads the current user.
3. For research requests, the backend reserves credits and creates a session.
4. The research pipeline performs search, scrape, synthesis, and export.
5. The session, credit transaction, and file export metadata are saved in MongoDB.
6. If a billing event arrives, the Razorpay webhook updates the subscription state and credits the user.

## Storage Model

MongoDB collections used by the server:

- `users`
- `credit_transactions`
- `research_sessions`
- `billing_plans`
- `billing_subscriptions`
- `billing_webhook_events`
- `file_assets`

## External Services

- Tavily: web search
- Gemini: answer generation
- Razorpay: subscriptions and webhooks
- Cloudinary: research export storage
