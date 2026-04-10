import uvicorn
from fastapi import FastAPI, Request, status, Form
from fastapi.responses import RedirectResponse
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from app.config import get_settings
from app.dependencies import IsUserLoggedIn, SessionDep, AuthDep
from fastapi.templating import Jinja2Templates
from app.utilities import get_flashed_messages
from jinja2 import Environment, FileSystemLoader
from sqlmodel import select
from app.models import User, Student, Review
from app.utilities import flash, create_access_token
from fastapi.staticfiles import StaticFiles
from typing import List

app = FastAPI(middleware=[
    Middleware(SessionMiddleware, secret_key=get_settings().secret_key)
])
template_env = Environment(loader=FileSystemLoader("app/templates"))
template_env.globals['get_flashed_messages'] = get_flashed_messages
templates = Jinja2Templates(env=template_env)
static_files = StaticFiles(directory="app/static")
app.mount("/static", static_files, name="static")


@app.get('/', response_class=RedirectResponse)
async def index_view(
  request: Request,
  user_logged_in: IsUserLoggedIn,
):
  if user_logged_in:
    return RedirectResponse(url=request.url_for('home_view'), status_code=status.HTTP_303_SEE_OTHER)
  return RedirectResponse(url=request.url_for('login_view'), status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login")
async def login_view(
  user_logged_in: IsUserLoggedIn,
  request: Request,
):
  if user_logged_in:
    return RedirectResponse(url=request.url_for('home_view'), status_code=status.HTTP_303_SEE_OTHER)
  return templates.TemplateResponse(
          request=request, 
          name="login.html",
      )

@app.post('/login')
def login_action(
  request: Request,
  db: SessionDep,
  username: str = Form(),
  password: str = Form(),
):
  user = db.exec(select(User).where(User.username == username)).one_or_none()
  if user and user.check_password(password):
    response = RedirectResponse(url=request.url_for("index_view"), status_code=status.HTTP_303_SEE_OTHER)
    access_token = create_access_token(data={"sub": f"{user.id}"})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=False,
        samesite="lax",
        secure=True,
    )    
    return response
  else:
    flash(request, 'Invalid username or password')
    return RedirectResponse(url=request.url_for('login_view'), status_code=status.HTTP_303_SEE_OTHER)


@app.get('/app')
@app.get('/app/{student_id}')
def home_view(
  request: Request, 
  user: AuthDep,
  db: SessionDep,
  student_id: int = 820321819
):
  students = db.exec(select(Student)).all()
  
  selected_student = db.get(Student, student_id)
  
  if not selected_student:
      selected_student = db.get(Student, 820321819)
  
  if not selected_student:
      return templates.TemplateResponse(
          request=request, 
          name="index.html",
          context={
              "request": request,
              "user": user,
              "students": students,
              "selected_student": None,
              "reviews": [],
              "avg_rating": 0.0,
              "error": "No students found in the database"
          }
      )

  reviews = db.exec(
      select(Review).where(Review.student_id == selected_student.id)
  ).all()

  ratings = [r.rating for r in reviews]
  avg_rating = round(sum(ratings)/len(ratings), 1) if ratings else 0.0

  return templates.TemplateResponse(
          request=request, 
          name="index.html",
          context={
              "request": request,
              "user": user,
              "students": students,
              "selected_student": selected_student,
              "reviews": reviews,
              "avg_rating": avg_rating
          }
      )


@app.post('/app/{student_id}/review')
def create_review(
  request: Request,
  db: SessionDep,
  user: AuthDep,
  student_id: int,
  text: str = Form(),
  rating: int = Form()
):
  review = Review(
      text=text,
      rating=rating,
      student_id=student_id,
      author_id=user.id
  )
  db.add(review)
  db.commit()
  return RedirectResponse(url=request.url_for("home_view", student_id=student_id), status_code=status.HTTP_303_SEE_OTHER)


@app.get('/app/review/{review_id}/delete')
def delete_review(
  request: Request,
  db: SessionDep,
  user: AuthDep,
  review_id: int
):
  review = db.get(Review, review_id)
  if review and review.author_id == user.id:
    db.delete(review)
    db.commit()
  return RedirectResponse(url=request.url_for("home_view"), status_code=status.HTTP_303_SEE_OTHER)


@app.get('/logout')
async def logout(request: Request):
  response = RedirectResponse(url=request.url_for("login_view"), status_code=status.HTTP_303_SEE_OTHER)
  response.delete_cookie(
      key="access_token", 
      httponly=True,
      samesite="none",
      secure=True
  )
  flash(request, 'logged out')
  return response

