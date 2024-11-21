from fastapi import FastAPI
from . import data
from starlette.middleware.cors import CORSMiddleware


app = FastAPI()

# Add CORS middleware to allow cross-origin requests from your React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://custom-frontend.local:3000"],  # Add your React app URL here
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)
# Include the API routes
app.include_router(data.router)
