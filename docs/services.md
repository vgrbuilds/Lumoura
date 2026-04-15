# Services

## `UserService`

Location: [`server/src/services/user_service.py`](../server/src/services/user_service.py)

Responsibilities:

- create users
- authenticate logins
- update profile details
- change passwords
- disable accounts
- maintain account billing status

## `CreditService`

Location: [`server/src/services/credit_service.py`](../server/src/services/credit_service.py)

Responsibilities:

- create credit balances for new users
- reserve credits before a research run
- refund credits when a run fails
- grant credits from successful subscription events
- record credit transactions

## `ResearchSessionService`

Location: [`server/src/services/research_session_service.py`](../server/src/services/research_session_service.py)

Responsibilities:

- create pending sessions
- store completed answers
- store search results and preferences
- store export references
- list sessions for a user

## `ResearchPipeline`

Location: [`server/src/services/pipeline_service.py`](../server/src/services/pipeline_service.py)

Responsibilities:

- search via Tavily
- scrape source pages
- fallback to snippets when scraping fails
- pass context to the synthesizer

## `SynthesizerService`

Location: [`server/src/services/synthesizer_service.py`](../server/src/services/synthesizer_service.py)

Responsibilities:

- build the prompt
- inject research preferences
- send the prompt to Gemini

## `ResearchExportService`

Location: [`server/src/services/research_export_service.py`](../server/src/services/research_export_service.py)

Responsibilities:

- build a markdown export from the research result
- upload the export to Cloudinary when configured
- store export metadata in MongoDB

## `CloudinaryService`

Location: [`server/src/services/cloudinary_service.py`](../server/src/services/cloudinary_service.py)

Responsibilities:

- upload markdown exports as raw files
- sign Cloudinary upload requests
- stay optional if Cloudinary is not configured

## `BillingService`

Location: [`server/src/services/billing_service.py`](../server/src/services/billing_service.py)

Responsibilities:

- expose plan configuration
- sync the local plan to Razorpay
- create subscriptions
- verify and process Razorpay webhooks
- credit users when subscriptions charge

## `FileAssetService`

Location: [`server/src/services/file_asset_service.py`](../server/src/services/file_asset_service.py)

Responsibilities:

- store export file metadata
- list files by user
- fetch exports by session
