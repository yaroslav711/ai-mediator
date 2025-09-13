"""
Main API application entry point.
"""

from fastapi import FastAPI

app = FastAPI(
    title="AI Mediator API",
    description="API для AI медиатора отношений",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Mediator API"}
