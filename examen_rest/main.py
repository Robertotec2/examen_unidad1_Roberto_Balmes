from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal, get_db
from models import Laptop


class LaptopCreate(BaseModel):
    marca: str
    modelo: str
    ram_gb: int


class LaptopOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    marca: str
    modelo: str
    ram_gb: int
    disponible: bool


LAPTOPS_INICIALES = [
    {"marca": "Dell", "modelo": "Latitude 5440", "ram_gb": 16, "disponible": True},
    {"marca": "Lenovo", "modelo": "ThinkPad E14", "ram_gb": 8, "disponible": False},
    {"marca": "HP", "modelo": "ProBook 450", "ram_gb": 16, "disponible": True},
]


def carga_inicial():
    db = SessionLocal()
    try:
        if db.query(Laptop).count() == 0:
            for datos in LAPTOPS_INICIALES:
                db.add(Laptop(**datos))
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    carga_inicial()
    yield


app = FastAPI(title="API del laboratorio de cómputo", lifespan=lifespan)


@app.get("/")
def inicio():
    return {"mensaje": "API del laboratorio de cómputo"}


@app.get("/laptops", response_model=list[LaptopOut])
def listar_laptops(db: Session = Depends(get_db)):
    return db.query(Laptop).order_by(Laptop.id).all()


@app.get("/laptops/disponibles", response_model=list[LaptopOut])
def listar_disponibles(db: Session = Depends(get_db)):
    return db.query(Laptop).filter(Laptop.disponible == True).order_by(Laptop.id).all()


@app.get("/laptops/{laptop_id}", response_model=LaptopOut)
def obtener_laptop(laptop_id: int, db: Session = Depends(get_db)):
    laptop = db.query(Laptop).filter(Laptop.id == laptop_id).first()
    if laptop is None:
        raise HTTPException(status_code=404, detail="Laptop no encontrada")
    return laptop


@app.post("/laptops", response_model=LaptopOut, status_code=status.HTTP_201_CREATED)
def crear_laptop(datos: LaptopCreate, db: Session = Depends(get_db)):
    laptop = Laptop(marca=datos.marca, modelo=datos.modelo, ram_gb=datos.ram_gb, disponible=True)
    db.add(laptop)
    db.commit()
    db.refresh(laptop)
    return laptop
