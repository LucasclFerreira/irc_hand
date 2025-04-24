import uvicorn
import ee
from fastapi import FastAPI
from src.routes import hand_route

try:
    ee.Initialize(project="ee-irc")
except Exception as e:
    print(f"Erro na inicialização do Earth Engine: {e}")

app = FastAPI(
    title="HAND Report Generator API",
    description="API para processamento de relatórios HAND",
    version="0.1.0"
)

app.include_router(hand_route.router, prefix="/api/hand")

@app.get("/")
async def root():
    return {
        "message": "HAND Report Generator API",
        "endpoints": [
            "/api/hand/upload-hand"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )