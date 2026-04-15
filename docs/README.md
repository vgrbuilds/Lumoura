# Lumoura Documentation

This folder contains the project documentation for the backend, pipeline, billing, file storage, and deployment workflow.

## Contents

- [Architecture](./architecture.md)
- [API Reference](./api.md)
- [Workflow](./workflow.md)
- [Services](./services.md)
- [Data Model](./data-model.md)
- [Deployment](./deployment.md)
- [Usage Guide](./usage.md)

## Quick Summary

Lumoura is a research assistant platform with:

- authenticated user accounts
- credit-based research usage
- Razorpay subscriptions
- MongoDB persistence
- Cloudinary-backed research exports
- downloadable history and account activity

The client calls the FastAPI backend, the backend runs the research pipeline, stores the run, and returns the answer plus a saved export reference.
