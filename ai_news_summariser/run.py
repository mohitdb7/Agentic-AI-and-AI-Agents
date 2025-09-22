import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "rest_api.be_app:app",  # use module-style path
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info"
    )