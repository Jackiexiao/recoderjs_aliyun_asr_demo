import uvicorn

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=9527, reload=True, log_level="debug")