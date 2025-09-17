from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from database import Base

# --------------------
# Table des produits
# --------------------
class Ecommerce(Base):
    __tablename__ = "marketProduit"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    description = Column(String, nullable=True)
    prix = Column(Integer, nullable=False)
    types = Column(String)
    quantite = Column(Integer)
    statut = Column(Boolean, default=False)
    image = Column(String, nullable=True)

    # Relations
    stock = relationship("Stock", back_populates="produit", uselist=False)
    paniers = relationship("Panier", back_populates="produit")


# --------------------
# Table Stock
# --------------------
class Stock(Base):
    __tablename__ = "stock"

    id = Column(Integer, primary_key=True, index=True)
    produit_id = Column(Integer, ForeignKey("marketProduit.id"), unique=True)
    quantite_disponible = Column(Integer, nullable=False, default=0)
    date_modification = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    produit = relationship("Ecommerce", back_populates="stock")


# --------------------
# Table Panier
# --------------------
class Panier(Base):
    __tablename__ = "paniers"

    id = Column(Integer, primary_key=True, index=True)
    produit_id = Column(Integer, ForeignKey("marketProduit.id"))

    # Copie d'infos produit
    nom_produit = Column(String, nullable=False)
    description = Column(String, nullable=True)
    prix = Column(Integer, nullable=False)   # prix unitaire
    quantite = Column(Integer, nullable=False)

    # Relations
    produit = relationship("Ecommerce", back_populates="paniers")
    caisses = relationship("Caisse", back_populates="panier")

    @property
    def total(self):
        return self.quantite * self.prix


# --------------------
# Table Caisse
# --------------------
class Caisse(Base):
    __tablename__ = "caisses"

    id = Column(Integer, primary_key=True, index=True)
    panier_id = Column(Integer, ForeignKey("paniers.id"))
    nom_produit = Column(String)
    description = Column(String, nullable=True)
    prix = Column(Integer, nullable=False)
    quantite = Column(Integer, nullable=False)

    # Relation avec le panier
    panier = relationship("Panier", back_populates="caisses")

    @property
    def total(self):
        return self.quantite * self.prix


