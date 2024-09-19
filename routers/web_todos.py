import sys
sys.path.append("..")

from starlette import status
from starlette.responses import RedirectResponse

from fastapi import Depends, APIRouter, Path, HTTPException, Request, Form, Query
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from routers.web_auth import get_current_user
from datetime import datetime


from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter(
    prefix="/todos",
    tags=["todos"],
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

    return templates.TemplateResponse("todos.html", {"request": request, "todos": todos,  "uzm": uzm, "sek": sek, "mus": mus, "chg": chg, "sts": sts, "user": user})



@router.get("/todos_add", response_class=HTMLResponse)
async def todos_new_add(request: Request,
                       db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    if user.get('user_role') == 'user':
        uzm = db.query(models.Users).filter(models.Users.id == user.get("id")).all()

    if user.get('user_role') == 'admin':
        uzm = db.query(models.Users).filter(models.Users.uzman == True and models.Users.is_active == True and models.Users.is_delete == False ).all()


    sek = db.query(models.Users).filter(models.Users.sekreter == True and models.Users.is_active == True and models.Users.is_delete == False).all()
    mus = db.query(models.Customers).filter(models.Customers.is_active == True and models.Customers.is_delete == False).all()
    chg = db.query(models.Charge).filter(models.Charge.is_active == True and models.Charge.is_delete == False).all()
    sts = db.query(models.Status).filter(models.Status.is_active == True and models.Status.is_delete == False).all()

    return templates.TemplateResponse("todos_add.html", {"request": request, "uzm": uzm, "sek": sek, "mus": mus, "chg": chg, "sts": sts, "user": user})


@router.post("/todos_add", response_class=HTMLResponse)
async def todos_create(request: Request,
                        start_time: str = Form(...),
                        end_time: str = Form(...),
                        uzman_id: int = Form(...),
                        sekreter_id: int = Form(...),
                        musteri_id: int = Form(...),
                        charge_id: int = Form(0),
                        status_id: int = Form(0),
                        description: str = Form(...),

                        db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo_model = models.Todos()
    todo_model.start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')  # '%Y-%m-%d %H:%M'
    todo_model.end_time = datetime.strptime(end_time, '%Y-%m-%dT%H:%M')  # '%Y-%m-%d %H:%M'
    todo_model.uzman_id = uzman_id
    todo_model.sekreter_id = sekreter_id
    todo_model.musteri_id = musteri_id
    todo_model.charge_id = charge_id
    todo_model.status_id = status_id
    todo_model.description = description

    db.add(todo_model)
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)




@router.get("/todos_edit/{todo_id}", response_class=HTMLResponse)
async def todo_edit(request: Request,
                    todo_id: int,
                    db: Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    if user.get('user_role') == 'user':
        uzm = db.query(models.Users).filter(models.Users.id == user.get("id")).all()

    if user.get('user_role') == 'admin':
        uzm = db.query(models.Users).filter(models.Users.uzman == True and models.Users.is_active == True and models.Users.is_delete == False ).all()

    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    sek = db.query(models.Users).filter(models.Users.sekreter == True and models.Users.is_active == True and models.Users.is_delete == False).all()
    mus = db.query(models.Customers).filter(models.Customers.is_active == True and models.Customers.is_delete == False).all()
    chg = db.query(models.Charge).filter(models.Charge.is_active == True and models.Charge.is_delete == False).all()
    sts = db.query(models.Status).filter(models.Status.is_active == True and models.Status.is_delete == False).all()

    return templates.TemplateResponse("todos_edit.html", {"request": request, "todo": todo, "uzm": uzm, "mus": mus, "sek": sek, "chg": chg, "sts": sts, "user": user})


@router.post("/todos_edit/{todo_id}", response_class=HTMLResponse)
async def todos_edit_commit(request: Request,
                            todo_id: int,
                            description: str = Form(...),
                            start_time: str = Form(...),
                            end_time: str = Form(...),
                            uzman_id: int = Form(...),
                            sekreter_id: int = Form(...),
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

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)







@router.get("/delete/{todo_id}")
async def delete_todo(request: Request,
                      todo_id: int,
                      db: Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)



    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()

    if todo_model is None:
        return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

    db.query(models.Todos).filter(models.Todos.id == todo_id).update({models.Todos.is_delete: True})

    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)







#_hard_delete
@router.get("/hard_delete/{todos_id}")
async def todos_hard_delete(request: Request,
                      todos_id: int,
                      db: Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)


    todos_model = db.query(models.Todos).filter(models.Todos.id == todos_id).first()


    if todos_model is None:
        return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

    db.query(models.Todos).filter(models.Todos.id == todos_id).delete()

    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)










