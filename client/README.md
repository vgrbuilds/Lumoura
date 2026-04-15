# Lumoura Client

A simple React + Ant Design + Tailwind client for the Lumoura backend.

## Local Setup

1. Install dependencies:

```bash
npm install
```

2. Make sure `client/.env` contains your deployed backend URL:

```env
DEPLOYED_SERVER_URL=https://your-backend-url.onrender.com/
```

3. Start the dev server:

```bash
npm run dev
```

## Build

```bash
npm run build
```

## Vercel

Deploy the `client` folder as a Vercel project.

No Docker is needed for the client.

If you change the backend URL later, update `DEPLOYED_SERVER_URL` in the client env file and redeploy.
