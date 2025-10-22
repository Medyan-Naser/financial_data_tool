from fastapi import FastAPI
from . import data
from starlette.middleware.cors import CORSMiddleware


app = FastAPI()

# Add CORS middleware to allow cross-origin requests from your React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://bird-view.local:3000"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)
# Include the API routes
app.include_router(data.router)
