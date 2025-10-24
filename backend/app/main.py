from fastapi import FastAPI
from . import data
from . import ai_endpoints
from . import macro_endpoints
from . import financials_cached
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
# NOTE: Order matters! More specific routes must come first
app.include_router(financials_cached.router)  # New cached financials with progress tracking (more specific)
app.include_router(data.router)  # Legacy data endpoints (less specific)
app.include_router(ai_endpoints.router)
app.include_router(macro_endpoints.router)
