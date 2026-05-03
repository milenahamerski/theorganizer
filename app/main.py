from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes import router

app = FastAPI()

# Configuração para servir arquivos estáticos (CSS, JS, Imagens)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configuração do diretório de templates HTML
templates = Jinja2Templates(directory="app/templates")

app.include_router(router)


@app.get("/")
async def serve_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.on_event("startup")
def startup():
    print("[APP] API iniciada com sucesso (DB e Frontend prontos!)")
