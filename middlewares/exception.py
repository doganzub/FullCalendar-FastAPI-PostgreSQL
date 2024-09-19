from traceback import print_exception
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI, Request

# Initialize FastAPI application
app = FastAPI()

# Custom middleware to handle exceptions globally
class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            # Attempt to process the incoming request and pass it to the next middleware or route handler
            return await call_next(request)
        except Exception as e:
            # If an exception occurs, print the traceback details to the console
            print_exception(e)
            # Return a JSON response with status code 500 (Internal Server Error)
            return JSONResponse(
                status_code=500,
                content={
                    'error': e.__class__.__name__,  # Include the exception class name in the response
                    'messages': e.args  # Include the error message(s) in the response
                }
            )
