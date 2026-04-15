# Workflow

## 1. Registration and Login

1. The user registers with name, email, and password.
2. The backend hashes the password and creates a user record in MongoDB.
3. The backend returns a JWT access token.
4. On login, the backend validates the password and returns a new token.

## 2. Research Run

1. The authenticated user submits a research query plus optional preferences.
2. The backend creates a pending research session.
3. Credits are reserved from the user account.
4. The research pipeline searches Tavily.
5. The pipeline scrapes up to `max_sources` pages.
6. The synthesizer builds a prompt using the query, sources, and preferences.
7. Gemini produces the answer.
8. The backend creates a markdown export.
9. The export is uploaded to Cloudinary if credentials are configured.
10. The session is updated with the answer, source list, preferences, and export metadata.
11. The API returns the final research response.

## 3. Research Failure Flow

1. The backend still creates the session first.
2. Credits are reserved.
3. If the pipeline fails, the backend refunds the credits.
4. The session is marked as failed.

## 4. Subscription Flow

1. The user requests a subscription.
2. The backend syncs or reuses the Razorpay plan.
3. The backend creates a Razorpay subscription.
4. The user completes the checkout on Razorpay.
5. Razorpay sends webhook events to the backend.
6. When a charge succeeds, the backend grants credits and updates the subscription state.

## 5. Account History

The account screen can fetch:

- user profile
- total credits
- research history
- transaction history
- subscription history
- saved file exports

## 6. Export Workflow

1. Every successful research run generates a markdown export.
2. The export is uploaded to Cloudinary when configured.
3. A file asset record is saved in MongoDB.
4. The export can be retrieved by session ID or from account history.
