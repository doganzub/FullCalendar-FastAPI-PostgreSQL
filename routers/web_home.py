import sys
sys.path.append("..")

from starlette import status
from starlette.responses import RedirectResponse

from fastapi import Depends, APIRouter, Path, HTTPException, Request, Form, Query
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from routers.web_auth import get_current_user
from datetime import date, datetime


from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter(
    prefix="/home",
    tags=["home"],
    responses={404: {"description": "Not found"}}
)

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.get("/", response_class=HTMLResponse)
async def read_all_by_user(request: Request, db: Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    if user.get('user_role') == 'user':
        todos = db.query(models.Todos).filter(models.Todos.uzman_id == user.get("id")).all()

    if user.get('user_role') == 'admin':
        todos = db.query(models.Todos).all()


    uzm = db.query(models.Users).filter(models.Users.uzman == True and models.Users.is_active == True and models.Users.is_delete == False ).all()
    sek = db.query(models.Users).filter(models.Users.sekreter == True and models.Users.is_active == True and models.Users.is_delete == False).all()
    mus = db.query(models.Customers).filter(models.Customers.is_active == True and models.Customers.is_delete == False).all()
    chg = db.query(models.Charge).filter(models.Charge.is_active == True and models.Charge.is_delete == False).all()
    sts = db.query(models.Status).filter(models.Status.is_active == True and models.Status.is_delete == False).all()

    return templates.TemplateResponse("home.html", {"request": request, "todos": todos,  "uzm": uzm, "sek": sek, "mus": mus, "chg": chg, "sts": sts, "user": user})