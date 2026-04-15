# API Reference

Base URL:

- local: `http://127.0.0.1:8000`
- production: your deployed Render URL

Most endpoints require:

```http
Authorization: Bearer <JWT>
```

## Auth

### `POST /auth/register`

Creates a user account and returns a JWT.

Request:

```json
{
  "name": "Test User",
  "email": "test@example.com",
  "password": "Password123!"
}
```

### `POST /auth/login`

Authenticates an existing user and returns a JWT.

### `GET /auth/me`

Returns the authenticated user profile.

### `PATCH /auth/me`

Updates the authenticated user profile.

### `POST /auth/change-password`

Updates the password and returns a fresh token.

## Research

### `POST /research`

Runs the full research pipeline.

Request:

```json
{
  "query": "What is the future of renewable energy?",
  "preferences": {
    "tone": "analytical",
    "creativity": 3,
    "audience": "founders",
    "depth": "deep",
    "output_format": "report",
    "language": "English",
    "max_sources": 5,
    "extra_context": "Focus on policy, cost, and adoption challenges.",
    "include_citations": true
  }
}
```

Returns:

- final answer
- sources used
- preferences snapshot
- session ID
- transaction ID
- export metadata

### `GET /research?query=...`

Runs research using a query string for the authenticated user.

### `GET /research/credits/me`

Returns the current credit balance.

### `GET /research/sessions`

Returns research history for the authenticated user.

### `GET /research/sessions/{session_id}`

Returns a single research session.

### `GET /research/sessions/{session_id}/export`

Returns the saved export metadata for a research session.

## Billing

### `GET /billing/config`

Returns the public Razorpay key and the configured plan.

### `GET /billing/plans`

Returns the local billing plan catalog.

### `POST /billing/plans/sync`

Syncs the configured plan to Razorpay.

### `POST /billing/subscriptions`

Creates a Razorpay subscription for the authenticated user.

Request:

```json
{
  "plan_code": "monthly",
  "customer_email": "test@example.com",
  "customer_contact": "9999999999"
}
```

### `GET /billing/subscriptions/me`

Returns all subscriptions for the authenticated user.

### `GET /billing/subscriptions/summary`

Returns a compact subscription summary.

### `POST /billing/webhooks/razorpay`

Receives Razorpay webhook notifications.

## Account

### `GET /account/me`

Returns the authenticated user profile.

### `GET /account/overview`

Returns aggregate counts for credits, sessions, transactions, subscriptions, and files.

### `GET /account/research`

Returns the user research history.

### `GET /account/transactions`

Returns the credit transaction history.

### `GET /account/subscriptions`

Returns the subscription history.

### `GET /account/files`

Returns the file export history.

### `POST /account/disable`

Disables the authenticated account.

## Response Notes

- All authenticated routes return `401` if the JWT is missing or invalid.
- Research routes return `402` when the user lacks enough credits.
- Research failures refund credits when the debit has already succeeded.
