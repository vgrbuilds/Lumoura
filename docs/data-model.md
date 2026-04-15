# Data Model

## `users`

Core account and billing profile.

Important fields:

- `user_id`
- `name`
- `email`
- `password_hash`
- `credits`
- `plan_status`
- `plan_code`
- `subscription_status`
- `subscription_id`
- `token_version`
- `is_active`

## `research_sessions`

Stores each completed or failed research run.

Important fields:

- `user_id`
- `query`
- `answer`
- `sources`
- `search_results`
- `preferences`
- `credits_cost`
- `debit_transaction_id`
- `refund_transaction_id`
- `export`
- `status`

## `credit_transactions`

Stores credit debits and credits.

Important fields:

- `user_id`
- `session_id`
- `type`
- `amount`
- `reason`
- `metadata`

## `billing_plans`

Stores the local subscription plan definition and Razorpay plan ID.

## `billing_subscriptions`

Stores subscription lifecycle data and webhook-driven state updates.

## `billing_webhook_events`

Deduplication guard for Razorpay webhook events.

## `file_assets`

Stores export file metadata and Cloudinary references.

Important fields:

- `user_id`
- `session_id`
- `asset_type`
- `filename`
- `cloudinary_public_id`
- `cloudinary_url`
- `cloudinary_resource_type`
- `cloudinary_format`
- `bytes`
