from fastapi import FastAPI

app = FastAPI(
    title= " AI Customer Support Agent",
    version= "0.1.0",
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}