import sys
from typing import Annotated

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

sys.path.append("..")

from starlette import status
from starlette.responses import RedirectResponse, Response, JSONResponse
from fastapi import Request, APIRouter, Depends, File
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from datetime import datetime
from fastapi import Depends, APIRouter, Path, HTTPException, Request, Form, Query
from routers.web_auth import get_current_user
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json

router = APIRouter(
    prefix="/calendar",
    tags=["calendar"],
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


# Define a model for the event
class Event(BaseModel):
    id: int
    title: str
    start: str
    end: str


@router.get("/", response_class=HTMLResponse)
async def calendar(request: Request, db: Session = Depends(get_db)):
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

    return templates.TemplateResponse("calendar.html", {"request": request, "todos": todos,  "uzm": uzm, "sek": sek, "mus": mus, "chg": chg, "sts": sts, "user": user})


@router.get("/events", status_code=status.HTTP_200_OK)
async def read_events(
        request: Request,
        db: Session = Depends(get_db),
        status_id: int = Query(None)
):
    user = await get_current_user(request)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    query = (
        select(
            models.Todos.id,
            models.Todos.start_time,
            models.Todos.end_time,
            models.Todos.description,
            models.Todos.uzman_id,
            models.Customers.id,
            models.Customers.ad,
            models.Customers.soyad,
            models.Users.ad,
            models.Todos.status_id
        )
        .where(models.Todos.is_delete == False)
        .join(models.Todos.todos_users_uzman)
        .join(models.Todos.todos_customers)
        .order_by(models.Todos.id)
    )

    if user.get('user_role') == 'user':
        query = query.where(models.Todos.uzman_id == user.get("id"))

    if status_id is not None:
        query = query.where(models.Todos.status_id == status_id)

    result = db.execute(query).all()

    events = []
    for row in result:
        # Determine color based on status_id
        color = '#3788d8'  # Default color
        if row[9] == 0:  # Assuming status_id 1 corresponds to a certain status
            color = '#3788d8'  # Set color to yellow for this status
        elif row[9] == 1:  # Assuming status_id 2 corresponds to another status
            color = '#52b21f'  # Set color to green for this status

        elif row[9] == 2:  # Assuming status_id 2 corresponds to another status
            color = '#595654'  # Set color to green for this status

        elif row[9] == 3:
            color = '#de8b44'

        elif row[9] == 9:
            color = 'red'



        # Formatting end time
        end_time_str = row[2].strftime("%H:%M")  # ("%Y-%m-%d %H:%M:%S")

        event = {
            "id": row[0],
            "title": f" - {end_time_str}  {row[8]} {row[6]} {row[7]} {row[3]}",
            "start": row[1],
            "end": row[2],
            "uzman_id": row[4],
            "musteri_id": row[5],
            "status_id": row[9],
            "musteri_ad": row[6],
            "musteri_soyad": row[7],
            "uzman_ad": row[8],
            "description": row[3],
            "color": color  # Add color information to the event data
        }
        events.append(event)

    return events


@router.post("/event_add", response_class=HTMLResponse)
async def todos_create(request: Request,
                       description: str = Form(...),
                       start_time: str = Form(...),
                       end_time: str = Form(...),
                       uzman_id: int = Form(...),
                       sekreter_id: int = Form(3),
                       musteri_id: int = Form(...),
                       charge_id: int = Form(1),
                       status_id: int = Form(0),

                       db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo_model = models.Todos()
    todo_model.description = description
    todo_model.start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')  # '%Y-%m-%d %H:%M'
    todo_model.end_time = datetime.strptime(end_time, '%Y-%m-%dT%H:%M')  # '%Y-%m-%d %H:%M'
    todo_model.uzman_id = uzman_id
    todo_model.sekreter_id = sekreter_id
    todo_model.musteri_id = musteri_id
    todo_model.charge_id = charge_id
    todo_model.status_id = status_id

    db.add(todo_model)
    db.commit()

    return RedirectResponse(url="/calendar", status_code=status.HTTP_302_FOUND)


@router.delete("/events/{todo_id}", response_model=Event)
async def delete_todo(request: Request,
                      todo_id: int,
                      db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()

    if todo_model is None:
        return RedirectResponse(url="/calendar", status_code=status.HTTP_302_FOUND)

    db.delete(todo_model)
    db.commit()

    return RedirectResponse(url="/calendar", status_code=status.HTTP_302_FOUND)




@router.put("/{todo_id}", response_class=HTMLResponse)
async def event_edit_commit(request: Request,
                            todo_id: int,
                            description: str = Form(...),
                            start_time: str = Form(...),
                            end_time: str = Form(...),
                            uzman_id: int = Form(...),
                            sekreter_id: int = Form(3),
                            musteri_id: int = Form(...),
                            charge_id: int = Form(None),
                            status_id: int = Form(None),  # Change default to None

                            db: Session = Depends(get_db)):

    if charge_id is None:
        charge_id = 0  # Set default value to 0 if status_id is None

    if status_id is None:
        status_id = 0  # Set default value to 0 if status_id is None



    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    todo_model.description = description
    todo_model.start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')  # '%Y-%m-%d %H:%M'
    todo_model.end_time = datetime.strptime(end_time, '%Y-%m-%dT%H:%M')  # '%Y-%m-%d %H:%M'
    todo_model.uzman_id = uzman_id
    todo_model.sekreter_id = sekreter_id
    todo_model.musteri_id = musteri_id
    todo_model.charge_id = charge_id
    todo_model.status_id = status_id

    db.add(todo_model)
    db.commit()

    return RedirectResponse(url="/calendar", status_code=status.HTTP_302_FOUND)





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

    return RedirectResponse(url="/calendar", status_code=status.HTTP_302_FOUND)