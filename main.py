import models
from database import engine
from routers import web_auth, web_home, web_todos, web_customers, web_calendar, web_charges, web_documents
from starlette.staticfiles import StaticFiles
from starlette import status
from starlette.responses import RedirectResponse
from middlewares.exception import ExceptionHandlerMiddleware
from fastapi import FastAPI

# Initialize FastAPI application
app = FastAPI()

# Create database tables based on the models if they don't exist
models.Base.metadata.create_all(bind=engine)

# Mount the static files directory for serving static assets (e.g., CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Define the root endpoint that redirects to the home page
@app.get("/")
async def root():
    # Redirect to the /home route
    return RedirectResponse(url="/home", status_code=status.HTTP_302_FOUND)

# Add custom middleware to handle exceptions
app.add_middleware(ExceptionHandlerMiddleware)

# Include various routers for handling different sections of the web application
app.include_router(web_auth.router)        # Authentication routes
app.include_router(web_home.router)        # Home page routes
app.include_router(web_todos.router)       # Todo management routes
app.include_router(web_customers.router)   # Customer management routes
app.include_router(web_calendar.router)    # Calendar management routes
app.include_router(web_charges.router)     # Charge management routes
