from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from models import init_db
from routers import auth, users, follow, moments, moderation, match, chat, payment, cards, reports, notifications, feedback, site_config, dashboard

app = FastAPI(title="交友聊天")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# 挂载静态文件
import os
from config import UPLOAD_DIR
os.makedirs(os.path.join(UPLOAD_DIR, "public"), exist_ok=True)
app.mount("/public", StaticFiles(directory=os.path.join(UPLOAD_DIR, "public")), name="public")

# 注册路由
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

@app.get("/api/health")
def health():
    return {"status": "ok"}

init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
