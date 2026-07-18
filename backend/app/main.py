from fastapi import FastAPI

app = FastAPI(
    title="Dell AI Parts Inspector API",
    version="1.0.0",
    description="Backend API for Dell Parts Fraud Detection Hackathon"
)

@app.get("/")
def root():
    return {
        "message": "Dell AI Parts Inspector Backend is Running 🚀"
    }