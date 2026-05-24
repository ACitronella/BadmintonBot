import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.database import init_db
from backend.routers.bills import router as bills_router

app = FastAPI(title="Badminton Invoice LIFF")

init_db()
app.include_router(bills_router)


@app.get("/api/config")
def get_config():
    return {"liff_id": os.environ.get("MINI_APP_ID", "")}

DIST = Path("frontend/dist")

if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        # Let the API router handle /api/* — this only catches non-API paths
        file = DIST / full_path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(DIST / "index.html")
else:
    @app.get("/")
    def dev_root():
        return {"status": "ok", "note": "Run 'npm run build' in frontend/ to serve the app"}
