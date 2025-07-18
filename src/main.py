from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import timedelta
from .auth import security
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="src/static"), name="static")

templates = Jinja2Templates(directory="src/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("/auth/login.html", {"request": request})

@app.post("/token", response_model=security.Token)
async def login_for_access_token(form_data: security.OAuth2PasswordRequestForm = Depends()):
    user = security.authenticate_user(security.fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    response = RedirectResponse(url="/home", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

from fastapi import Cookie

async def get_token_from_cookie(access_token: str | None = Cookie(None)):
    if access_token is None:
        return None
    # The access_token from the cookie has the "Bearer " prefix, so we remove it
    return access_token.split(" ")[1]

@app.get("/home", response_class=HTMLResponse)
async def read_home(request: Request, token: str = Depends(get_token_from_cookie)):
    if token is None:
        return RedirectResponse(url="/auth/login")

    try:
        user = await security.get_current_active_user(await security.get_current_user(token))
    except Exception:
        return RedirectResponse(url="/auth/login")
    return templates.TemplateResponse("home.html", {"request": request, "username": user.username})

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("/auth/login.html", {"request": request})
