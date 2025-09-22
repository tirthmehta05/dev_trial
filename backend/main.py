from fastapi import FastAPI

app = FastAPI()

@app.get("/api/data")
def get_data():
    return {"message": "Hello from FastAPI!"}
