from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import os, shutil

from database import Session_Local, Base, Engine
from model import Ecommerce, Panier, Stock, Caisse

# --------------------
# Créer les tables
# --------------------
Base.metadata.create_all(bind=Engine)

app = FastAPI()

# --------------------
# CORS pour React
# --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------
# Upload images
# --------------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

# --------------------
# DB Session
# --------------------
def get_db():
    db = Session_Local()
    try:
        yield db
    finally:
        db.close()

# --------------------
# Schémas Pydantic
# --------------------
class EcommerceBase(BaseModel):
    nom: str
    description: str
    prix: int
    quantite: int
    statut: bool = False
    types: str
    image: Optional[str] = None

class EcommerceCreate(EcommerceBase):
    pass

class EcommerceOut(EcommerceBase):
    id: int
    class Config:
        orm_mode = True

class CommandeCreate(BaseModel):
    produit_id: int
    quantite: int

class CommandeOut(BaseModel):
    id: int
    produit_id: int
    nom_produit: str
    description: str
    quantite: int
    prix: int
    total: int
    class Config:
        orm_mode = True

# --------------------
# CRUD Ecommerce
# --------------------
@app.get("/Ecommerce/", response_model=List[EcommerceOut])
def get_all(db: Session = Depends(get_db)):
    return db.query(Ecommerce).all()

@app.get("/Ecommerce/{id}", response_model=EcommerceOut)
def get_one(id: int, db: Session = Depends(get_db)):
    obj = db.query(Ecommerce).filter(Ecommerce.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return obj

@app.post("/Ecommerce/", response_model=EcommerceOut)
async def create_product(
    nom: str = Form(...),
    description: str = Form(...),
    prix: int = Form(...),
    quantite: int = Form(...),
    statut: bool = Form(False),
    types: str = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    image_filename = None
    if image:
        image_filename = f"{nom}_{image.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, image_filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(image.file, f)
    new_obj = Ecommerce(
        nom=nom, description=description, prix=prix,
        quantite=quantite, statut=statut, types=types,
        image=image_filename
    )
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj

@app.put("/Ecommerce/{id}", response_model=EcommerceOut)
async def update_product(
    id: int,
    nom: str = Form(...),
    description: str = Form(...),
    prix: int = Form(...),
    quantite: int = Form(...),
    types: str = Form(...),
    statut: bool = Form(False),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    obj = db.query(Ecommerce).filter(Ecommerce.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    obj.nom = nom
    obj.description = description
    obj.prix = prix
    obj.quantite = quantite
    obj.types = types
    obj.statut = statut
    if image:
        image_filename = f"{nom}_{image.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, image_filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(image.file, f)
        obj.image = image_filename
    db.commit()
    db.refresh(obj)
    return obj

from fastapi import Body

from fastapi import Body

@app.put("/Ecommerce/{id}/quantite", response_model=EcommerceOut)
def update_quantite(id: int, quantite: int = Query(...), db: Session = Depends(get_db)):
    produit = db.query(Ecommerce).filter(Ecommerce.id == id).first()
    if not produit:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    produit.quantite = quantite
    db.commit()
    db.refresh(produit)
    return produit


@app.delete("/Ecommerce/{id}")
def delete_product(id: int, db: Session = Depends(get_db)):
    obj = db.query(Ecommerce).filter(Ecommerce.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    db.delete(obj)
    db.commit()
    return {"detail": "Produit supprimé"}

# --------------------
# CRUD Panier
# --------------------
@app.post("/Panier/", response_model=CommandeOut)
def ajouter_panier(panier: CommandeCreate, db: Session = Depends(get_db)):
    produit = db.query(Ecommerce).filter(Ecommerce.id == panier.produit_id).first()
    if not produit:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    if panier.quantite > produit.quantite:
        raise HTTPException(status_code=400, detail="Stock insuffisant")
    produit.quantite -= panier.quantite
    db.commit()
    new_item = Panier(
        produit_id=produit.id,
        nom_produit=produit.nom,
        description=produit.description,
        prix=produit.prix,
        quantite=panier.quantite
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return CommandeOut(
        id=new_item.id,
        produit_id=new_item.produit_id,
        nom_produit=new_item.nom_produit,
        description=new_item.description,
        quantite=new_item.quantite,
        prix=new_item.prix,
        total=new_item.quantite * new_item.prix
    )

@app.get("/Panier/", response_model=List[CommandeOut])
def lire_panier(db: Session = Depends(get_db)):
    return db.query(Panier).all()

@app.delete("/Panier/{id}")
def supprimer_panier(id: int, db: Session = Depends(get_db)):
    panier = db.query(Panier).filter(Panier.id == id).first()
    if not panier:
        raise HTTPException(status_code=404, detail="Panier non trouvé")
    db.delete(panier)
    db.commit()
    return {"message": f"Panier {id} supprimé"}

# --------------------
# Caisse / Tickets
# --------------------
@app.post("/Caisse/payer-tout")
def payer_tout(db: Session = Depends(get_db)):
    paniers = db.query(Panier).all()
    if not paniers:
        raise HTTPException(status_code=400, detail="Panier vide")
    tickets = []
    for panier in paniers:
        ticket = Caisse(
            panier_id=panier.id,
            nom_produit=panier.nom_produit,
            description=panier.description,
            prix=panier.prix,
            quantite=panier.quantite
        )
        db.add(ticket)
        tickets.append(ticket)
        db.delete(panier)
    db.commit()
    return [
        {
            "id": t.id,
            "nom_produit": t.nom_produit,
            "prix_unitaire": t.prix,
            "quantite": t.quantite,
            "total": t.prix * t.quantite
        }
        for t in tickets
    ]

@app.get("/Caisse/")
def historique_tickets(db: Session = Depends(get_db)):
    tickets = db.query(Caisse).all()
    return [
        {
            "id": t.id,
            "nom_produit": t.nom_produit,
            "prix_unitaire": t.prix,
            "quantite": t.quantite,
            "total": t.prix * t.quantite
        }
        for t in tickets
    ]


# Route pour récupérer les statistiques
from fastapi import Depends
from sqlalchemy.orm import Session

@app.get("/api/statistique")
def get_statistique(db: Session = Depends(get_db)):
    total_produits = db.query(Ecommerce).count()
    produits_actifs = db.query(Ecommerce).filter(Ecommerce.statut==True).count()
    produits_rupture = db.query(Ecommerce).filter(Ecommerce.quantite <= 0).count()
    chiffre_affaires = db.query(func.sum(Caisse.quantite * Caisse.prix)).scalar() or 0

    top_produits = db.query(
        Caisse.nom_produit,
        func.sum(Caisse.quantite).label("total_ventes")
    ).group_by(Caisse.nom_produit).order_by(func.sum(Caisse.quantite).desc()).limit(5).all()

    top_produits_list = [{"nom": p.nom_produit, "ventes": p.total_ventes} for p in top_produits]

    return {
        "total_produits": total_produits,
        "produits_actifs": produits_actifs,
        "produits_rupture": produits_rupture,
        "chiffre_affaires": chiffre_affaires,
        "top_produits": top_produits_list
    }

    total_produits = db.query(Ecommerce).count()
    produits_actifs = db.query(Ecommerce).filter(Ecommerce.statut==True).count()
    produits_rupture = db.query(Stock).filter(Stock.quantite_disponible <= 0).count()
    chiffre_affaires = db.query(func.sum(Caisse.quantite * Caisse.prix)).scalar() or 0

    # Produits les plus vendus
    top_produits = db.query(
        Panier.nom_produit,
        func.sum(Panier.quantite).label("total_ventes")
    ).group_by(Panier.nom_produit).order_by(func.sum(Panier.quantite).desc()).limit(5).all()

    # Transformation en liste dict pour React
    top_produits_list = [{"nom": p.nom_produit, "ventes": p.total_ventes} for p in top_produits]

    return {
        "total_produits": total_produits,
        "produits_actifs": produits_actifs,
        "produits_rupture": produits_rupture,
        "chiffre_affaires": chiffre_affaires,
        "top_produits": top_produits_list
    }