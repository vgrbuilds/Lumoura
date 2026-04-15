# Deployment

## Local Development

1. Set the environment variables in `server/.env`.
2. Start the stack with:

```powershell
docker compose up --build
```

This starts:

- MongoDB as a local replica set
- the FastAPI server container

## Render Deployment

Deploy the backend from `server/Dockerfile`.

Required environment variables:

- `GOOGLE_API_KEY`
- `TAVILY_API_KEY`
- `MONGO_URI`
- `JWT_SECRET`
- `RAZORPAY_TEST_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `RAZORPAY_WEBHOOK_SECRET`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`
- optional subscription tuning vars

## MongoDB

Use MongoDB Atlas or another replica-set-backed MongoDB instance for production.

Why:

- credit deductions use transactions
- billing updates use transactions
- session consistency is easier to maintain

## Cloudinary

Cloudinary is optional but recommended for storing exported research files.

If Cloudinary is not configured:

- the export file metadata still saves in MongoDB
- the API still returns research results
- only the remote file upload step is skipped

## Recommended Production Layout

- Frontend: Vercel, Netlify, or similar
- Backend: Render
- Database: MongoDB Atlas
- File storage: Cloudinary
- Payments: Razorpay
