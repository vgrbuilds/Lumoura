from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.account import router as account_router
from src.api.auth import router as auth_router
from src.api.billing import router as billing_router
from src.api.research import router as research_router
from src.core.config import CORS_ALLOW_VERCEL_PREVIEWS, CORS_ORIGINS, CORS_VERCEL_PREVIEW_REGEX


app = FastAPI(title="Lumoura Research API", version="0.1.0")

allow_origins = ["*"] if "*" in CORS_ORIGINS else CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=CORS_VERCEL_PREVIEW_REGEX if CORS_ALLOW_VERCEL_PREVIEWS else None,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research_router)
app.include_router(billing_router)
app.include_router(auth_router)
app.include_router(account_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
