import json
import os
import shutil
import sys

from fastapi.encoders import jsonable_encoder

sys.path.append("..")

from typing import Annotated
from passlib.context import CryptContext

from starlette import status
from starlette.responses import RedirectResponse
from fastapi import Depends, APIRouter, Request, Form, File, UploadFile
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel
from routers.web_auth import get_current_user

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
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


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class UserVerification(BaseModel):
    username: str
    password: str
    new_password: str


@router.get("/", response_class=HTMLResponse)
async def read_by_user(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    # customers = db.query(models.Customers).filter(models.Customers.id == customer.get("id")).all()
    customers = db.query(models.Customers).all()

    return templates.TemplateResponse("customers.html", {"request": request, "customers": customers, "user": user})


@router.get("/customers_add", response_class=HTMLResponse)
async def add_new_customers(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    customers = db.query(models.Customers)
    return templates.TemplateResponse("customers_add.html", {"request": request, "customers": customers, "user": user})


@router.post("/customers_add", response_class=HTMLResponse)
async def create_customers(request: Request,
                           tc: int = Form(...),
                           ad: str = Form(...),
                           soyad: str = Form(...),
                           email: str = Form(...),
                           telno: str = Form(...),
                           info: str = Form('test'),
                           address1: str = Form('test'),
                           city: str = Form('test'),
                           url: Annotated[str | None, File()] = None,
                           db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    customers_model = models.Customers()
    customers_model.tc = tc
    customers_model.ad = ad
    customers_model.soyad = soyad
    customers_model.email = email
    customers_model.telno = telno
    customers_model.info = info
    customers_model.address1 = address1
    customers_model.city = city
    customers_model.url = url
    customers_model.is_active = True
    customers_model.is_delete = False

    db.add(customers_model)
    db.commit()

    return RedirectResponse(url="/customers", status_code=status.HTTP_302_FOUND)


@router.get("/customers_edit/{customer_id}", response_class=HTMLResponse)
async def customers_edit(request: Request,
                         customer_id: int,
                         db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    customers = db.query(models.Customers)
    customer = db.query(models.Customers).filter(models.Customers.id == customer_id).first()
    document = db.query(models.Documents).filter(models.Documents.customer_id == customer_id).first()

    return templates.TemplateResponse("customers_edit.html",
                                      {"request": request, "customer": customer, "customers": customers,
                                       "document": document, "user": user})



@router.post("/customers_edit/{customer_id}", response_class=HTMLResponse)
async def customers_edit_commit(request: Request,
                                customer_id: int,
                                tc: int = Form(...),
                                ad: str = Form(...),
                                soyad: str = Form(...),
                                email: str = Form(...),
                                telno: str = Form(...),
                                info: str = Form('test'),
                                address1: str = Form('test'),
                                city: str = Form('test'),
                                url: str = Form('test'),
                                db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    customers_model = db.query(models.Customers).filter(models.Customers.id == customer_id).first()

    customers_model.tc = tc
    customers_model.ad = ad
    customers_model.soyad = soyad
    customers_model.email = email
    customers_model.telno = telno
    customers_model.info = info
    customers_model.address1 = address1
    customers_model.city = city
    customers_model.url = url
    customers_model.is_active = True
    customers_model.is_delete = False

    db.add(customers_model)
    db.commit()

    msg = "Successfuly uploaded"

    return RedirectResponse(url=f"/customers/customers_edit/{customer_id}?msg={msg}", status_code=status.HTTP_302_FOUND)




@router.get("/delete/{customer_id}")
async def customers_delete(request: Request,
                           customer_id: int,
                           db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    customer = db.query(models.Customers).filter(models.Customers.id == customer_id).first()


    db.query(models.Customers).filter(models.Customers.id == customer_id).update({models.Customers.is_delete: True})

    db.commit()

    msg = f"Deleted {customer.ad} {customer.soyad} "

    return RedirectResponse(url=f"/customers/?msg={msg}", status_code=status.HTTP_302_FOUND)