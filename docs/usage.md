# Usage Guide

## 1. Create an Account

Call `POST /auth/register` with name, email, and password.

## 2. Log In

Call `POST /auth/login` to get a JWT.

## 3. Run Research

Use the JWT in the `Authorization` header and call `POST /research`.

You can control:

- tone
- creativity
- audience
- depth
- output format
- language
- max sources
- extra context
- citations

## 4. Review Results

Use:

- `GET /research/sessions`
- `GET /research/sessions/{session_id}`
- `GET /research/sessions/{session_id}/export`

## 5. Check Credits

Use `GET /research/credits/me` or `GET /account/overview`.

## 6. Subscribe

Use `POST /billing/subscriptions` with the authenticated user.

Webhook events from Razorpay will automatically credit the account.

## 7. Review History

Use:

- `GET /account/research`
- `GET /account/transactions`
- `GET /account/subscriptions`
- `GET /account/files`

## 8. Disable Account

Use `POST /account/disable`.
