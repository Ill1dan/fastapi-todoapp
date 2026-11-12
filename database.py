from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URI = 'sqlite:///./todosapp.db'
SQLALCHEMY_DATABASE_URI_POSTGRESQL = 'postgresql://postgres:nanam@localhost/TodoApplicationDatabase'
SQLALCHEMY_DATABASE_URI_MYSQL = 'mysql+pymysql://root:password@127.0.0.1:3306/TodoApplicationDatabase'

engine = create_engine(SQLALCHEMY_DATABASE_URI) # connect_args={"check_same_thread": False} For SQLite only

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()