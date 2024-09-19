import sys
sys.path.append("..")

from typing import Annotated
from passlib.context import CryptContext


from starlette import status
from starlette.responses import RedirectResponse
from fastapi import Depends, APIRouter, Request, Form
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel
from routers.web_auth import get_current_user

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter(
    prefix="/charges",
    tags=["charges"],
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

    #charges = db.query(models.charges).filter(models.charges.id == customer.get("id")).all()
    charge = db.query(models.Charge).all()

    return templates.TemplateResponse("charges.html", {"request": request, "charge": charge, "user": user})


@router.get("/charges_add", response_class=HTMLResponse)
async def add_new_charges(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    charge = db.query(models.Charge)
    return templates.TemplateResponse("charges_add.html", {"request": request, "charge": charge, "user": user})



@router.post("/charges_add", response_class=HTMLResponse)
async def create_charges(request: Request,
                         net: int = Form(...),
                         tax: int = Form(...),
                         charge_name: str = Form(...),
                         is_active: bool = Form(False),
                         db: Session = Depends(get_db)):


    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    charge_model = models.Charge()
    charge_model.net = net
    charge_model.tax = net * (tax/100)
    charge_model.total = net + (net * (tax/100))
    charge_model.charge_name = charge_name
    charge_model.is_active = is_active
    charge_model.is_delete = False



    db.add(charge_model)
    db.commit()

    return RedirectResponse(url="/charges", status_code=status.HTTP_302_FOUND)



@router.get("/charges_edit/{charge_id}", response_class=HTMLResponse)
async def charges_edit(request: Request,
                    charge_id: int,
                    db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    charge = db.query(models.Charge).filter(models.Charge.id == charge_id).first()

    return templates.TemplateResponse("charges_edit.html", {"request": request, "charge": charge, "user": user})


@router.post("/charges_edit/{charge_id}", response_class=HTMLResponse)
async def charges_edit_commit(request: Request,
                            charge_id: int,
                            net: int = Form(...),
                            tax: int = Form(...),
                            charge_name: str = Form(...),
                            is_active: bool = Form(...),
                            db: Session = Depends(get_db)):


    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    charge_model = db.query(models.Charge).filter(models.Charge.id == charge_id).first()

    charge_model.net = net
    charge_model.tax = net * (tax/100)
    charge_model.total = net + (net * (tax/100))
    charge_model.charge_name = charge_name
    charge_model.is_active = is_active
    charge_model.is_delete = False


    db.add(charge_model)
    db.commit()

    return RedirectResponse(url="/charges", status_code=status.HTTP_302_FOUND)





@router.get("/delete/{charge_id}")
async def charges_delete(request: Request,
                      charge_id: int,
                      db: Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    charge_model = db.query(models.Charge).filter(models.Charge.id == charge_id).first()

    if charge_model is None:
        return RedirectResponse(url="/charges", status_code=status.HTTP_302_FOUND)

    db.query(models.Charge).filter(models.Charge.id == charge_id).update({models.Charge.is_delete: True})

    db.commit()

    return RedirectResponse(url="/charges", status_code=status.HTTP_302_FOUND)




#_hard_delete: customer db den siliniyor
@router.get("/hard_delete/{charge_id}")
async def charges_hard_delete(request: Request,
                      charge_id: int,
                      db: Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)


    charge_model = db.query(models.Charge).filter(models.Charge.id == charge_id).first()


    if charge_model is None:
        return RedirectResponse(url="/charges", status_code=status.HTTP_302_FOUND)

    db.query(models.Charge).filter(models.Charge.id == charge_id).delete()

    db.commit()

    return RedirectResponse(url="/charges", status_code=status.HTTP_302_FOUND)





