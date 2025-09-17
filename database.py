from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


Database_Url = "sqlite:///./Ecommerce.db"

Engine = create_engine(Database_Url,connect_args={"check_same_thread":False})
Session_Local = sessionmaker(autocommit = False,autoflush=False,bind=Engine)

Base = declarative_base()

