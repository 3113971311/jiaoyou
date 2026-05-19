import os
import warnings

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import ALLOWED_CORS_ORIGINS, CARD_PEPPER, JWT_SECRET, UPLOAD_DIR
from models import init_db
from routers import auth, cards, chat, dashboard, feedback, follow, match, moderation, moments, notifications, payment, reports, site_config, users, verify

app = FastAPI(title="拾光")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(os.path.join(UPLOAD_DIR, "public"), exist_ok=True)
app.mount("/public", StaticFiles(directory=os.path.join(UPLOAD_DIR, "public")), name="public")

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(follow.router, prefix="/api")
app.include_router(moments.router, prefix="/api")
app.include_router(moderation.router, prefix="/api")
app.include_router(match.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(payment.router, prefix="/api")
app.include_router(cards.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(site_config.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(verify.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}


init_db()

if JWT_SECRET in {"dev-secret-key", "change-me-secret-key"}:
    warnings.warn("JWT_SECRET 仍为弱默认值，请尽快更换生产密钥。", RuntimeWarning)
if CARD_PEPPER in {"dev-card-pepper", "change-me-card-pepper"}:
    warnings.warn("CARD_PEPPER 仍为弱默认值，请尽快更换生产密钥。", RuntimeWarning)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
