import sys
sys.path.append("..")

from typing import Annotated, Optional
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer # For handling OAuth2 authentication
from datetime import timedelta, datetime
from jose import jwt, JWTError # For JWT encoding and decoding

from fastapi import HTTPException, Response, Depends, APIRouter, Request, Form
from models import Users
from passlib.context import CryptContext # For password hashing and verification

from starlette import status
from starlette.responses import RedirectResponse
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Secret key and algorithm for JWT token encoding/decoding (ensure this is securely stored)
SECRET_KEY = 'your_secret_key_here'
ALGORITHM = 'HS256'

# Directory for Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Password hashing context using bcrypt
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create all database tables if they do not exist
models.Base.metadata.create_all(bind=engine)

# OAuth2 scheme for token-based authentication
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")

# FastAPI Router for authentication-related routes
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"user": "Not authorized"}}
)

# Class to handle login form data
class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    # Function to parse the form data
    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get("email")
        self.password = form.get("password")

# Dependency to get a new database session for each request
def get_db():
    db = SessionLocal() # Create a local session for each request
    try:
        yield db
    finally:
        db.close() # Close the session after the request is handled

# Dependency for injecting the database session into routes
db_dependency = Annotated[Session, Depends(get_db)]

# Function to hash a plain text password
def get_password_hash(password):
    return bcrypt_context.hash(password)

# Function to verify if the plain password matches the hashed password
def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)

# Function to authenticate a user by username and password
def authenticate_user(username: str, password: str, db):
    user = db.query(models.Users).filter(models.Users.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

# Function to create a JWT token for authenticated users
def create_access_token(username: str,
                        user_id: int,
                        role: str,
                        expires_delta: Optional[timedelta] = None):
    encode = {"sub": username, "id": user_id, 'role': role}
    expire = datetime.utcnow() + expires_delta if expires_delta else datetime.utcnow() + timedelta(minutes=30)
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

# Function to retrieve the current authenticated user by decoding the JWT token
async def get_current_user(request: Request):
    try:
        token = request.cookies.get("access_token")
        if not token:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        user_id = payload.get("id")
        user_role = payload.get('role')
        if not username or not user_id:
            logout(request)
        return {'username': username, 'id': user_id, 'user_role': user_role}
    except JWTError:
        raise HTTPException(status_code=404, detail="Not found")

# Route to handle user login and token generation
@router.post("/token")
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return False
    token_expires = timedelta(minutes=60)
    token = create_access_token(user.username, user.id, user.role, expires_delta=token_expires)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return True

# Route to render the login page
@router.get("/", response_class=HTMLResponse)
async def authentication_page(request: Request):
    return templates.TemplateResponse("auth_login.html", {"request": request})

# Route to handle the login form submission
@router.post("/", response_class=HTMLResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    try:
        form = LoginForm(request)
        await form.create_oauth_form()
        response = RedirectResponse(url="/home", status_code=status.HTTP_302_FOUND)

        validate_user_cookie = await login_for_access_token(response=response, form_data=form, db=db)

        if not validate_user_cookie:
            msg = "Incorrect Username or Password"
            return templates.TemplateResponse("auth_login.html", {"request": request, "msg": msg})
        return response
    except HTTPException:
        msg = "Unknown Error"
        return templates.TemplateResponse("auth_login.html", {"request": request, "msg": msg})

# Route to handle user logout and clear the authentication cookie
@router.get("/logout")
async def logout(request: Request):
    msg = "Logout Successful"
    response = templates.TemplateResponse("auth_login.html", {"request": request, "msg": msg})
    response.delete_cookie(key="access_token")
    return response

# Other routes related to user registration, password change, and user management follow here...

# Example of password change route:
@router.post("/new_password", response_class=HTMLResponse)
async def user_password_change(request: Request,
                               username: str = Form(...),
                               password: str = Form(...),
                               password2: str = Form(...),
                               db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    user_data = db.query(models.Users).filter(models.Users.username == username).first()
    msg = "Invalid username or password"

    if user_data and verify_password(password, user_data.hashed_password):
        user_data.hashed_password = get_password_hash(password2)
        db.add(user_data)
        db.commit()
        msg = 'Password updated'

    return templates.TemplateResponse("home.html", {"request": request, "user": user, "msg": msg})

# Route to render the user registration page (only accessible to admins)
@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    try:
        if user.get('user_role') == 'admin':
            msg = "Admin permission granted"
            return templates.TemplateResponse("auth_register.html", {"request": request, "user": user, "msg": msg})

        # Redirect if user is not an admin
        response = RedirectResponse(url="/home", status_code=status.HTTP_302_FOUND)

        if user.get('user_role') == 'user':
            msg = "You do not have access permission"
            return templates.TemplateResponse("auth_warning.html", {"request": request, "user": user, "msg": msg})

        return response
    except HTTPException:
        msg = "Unknown Error"
        return templates.TemplateResponse("auth_login.html", {"request": request, "msg": msg})

# Route to handle user registration form submission (for admins to register new users)
@router.post("/register", response_class=HTMLResponse)
async def register_user(request: Request,
                        email: str = Form(...),
                        username: str = Form(...),
                        tc: int = Form(...),
                        ad: str = Form(...),
                        soyad: str = Form(...),
                        telno: str = Form(...),
                        password: str = Form(...),
                        password2: str = Form(...),
                        role: str = Form(...),
                        owner: bool = Form(False),
                        uzman: bool = Form(False),
                        sekreter: bool = Form(False),
                        is_active: bool = Form(False),
                        is_delete: bool = Form(False),
                        db: Session = Depends(get_db)):
    
    # Check if username or email already exists
    validation1 = db.query(models.Users).filter(models.Users.username == username).first()
    validation2 = db.query(models.Users).filter(models.Users.email == email).first()

    # If passwords don't match or user already exists, show error message
    if password != password2 or validation1 is not None or validation2 is not None:
        msg = "Invalid registration request"
        return templates.TemplateResponse("auth_register.html", {"request": request, "msg": msg})

    # Create a new user
    user_model = models.Users()
    user_model.email = email
    user_model.username = username
    user_model.tc = tc
    user_model.ad = ad
    user_model.soyad = soyad
    user_model.telno = telno
    user_model.role = role
    user_model.owner = owner
    user_model.uzman = uzman
    user_model.sekreter = sekreter
    user_model.is_active = is_active
    user_model.is_delete = is_delete

    # Hash the user's password and activate the user
    hash_password = get_password_hash(password)
    user_model.hashed_password = hash_password
    user_model.is_active = True

    # Add the new user to the database
    db.add(user_model)
    db.commit()

    msg = "User successfully created"

    # After successful registration, return all users for admin
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    users = db.query(models.Users).all()
    return templates.TemplateResponse("auth_users.html", {"request": request, "users": users, "user": user, "msg": msg})

# Route to list all users (only accessible to admins)
@router.get("/users", response_class=HTMLResponse)
async def read_by_user(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    # Query to get all users from the database
    users = db.query(models.Users).all()
    return templates.TemplateResponse("auth_users.html", {"request": request, "users": users, "user": user})

# Route to edit a specific user
@router.get("/users_edit/{users_id}", response_class=HTMLResponse)
async def users_edit(request: Request, users_id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    # Query to get the specific user to edit
    users = db.query(models.Users).filter(models.Users.id == users_id).first()
    return templates.TemplateResponse("auth_users_edit.html", {"request": request, "users": users, "user": user})

# Route to handle form submission for editing a user
@router.post("/users_edit/{users_id}", response_class=HTMLResponse)
async def users_edit_commit(request: Request,
                            users_id: int,
                            tc: int = Form(...),
                            ad: str = Form(...),
                            soyad: str = Form(...),
                            email: str = Form(...),
                            telno: str = Form(...),
                            password: str = Form(...),
                            role: str = Form(...),
                            owner: bool = Form(...),
                            uzman: bool = Form(...),
                            sekreter: bool = Form(...),
                            is_active: bool = Form(...),
                            db: Session = Depends(get_db)):
    
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    # Query to get the user model by ID
    users_model = db.query(models.Users).filter(models.Users.id == users_id).first()

    # Update user details
    users_model.tc = tc
    users_model.ad = ad
    users_model.soyad = soyad
    users_model.email = email
    users_model.telno = telno
    users_model.hashed_password = get_password_hash(password)
    users_model.role = role
    users_model.owner = owner
    users_model.uzman = uzman
    users_model.sekreter = sekreter
    users_model.is_active = is_active
    users_model.is_delete = False

    # Commit the changes to the database
    db.add(users_model)
    db.commit()

    return RedirectResponse(url="/auth/users", status_code=status.HTTP_302_FOUND)

# Route to soft delete a user (mark user as deleted)
@router.get("/delete/{users_id}")
async def users_delete(request: Request, users_id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    # Query to soft delete the user
    db.query(models.Users).filter(models.Users.id == users_id).update({models.Users.is_delete: True})
    db.commit()

    return RedirectResponse(url="/auth/users", status_code=status.HTTP_302_FOUND)

# Route to hard delete a user (permanently remove user from database)
@router.get("/hard_delete/{users_id}")
async def users_hard_delete(request: Request, users_id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    # Query to permanently delete the user
    db.query(models.Users).filter(models.Users.id == users_id).delete()
    db.commit()

    return RedirectResponse(url="/auth/users", status_code=status.HTTP_302_FOUND)

