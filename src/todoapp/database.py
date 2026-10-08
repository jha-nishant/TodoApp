from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DB_PATH = Path(__file__).resolve().parent / 'todosapp.db'
SQLALCHEMY_DATABASE_URL = f'sqlite:///{DB_PATH}'
# By default, Python's sqlite3 module raises an error if a connection is used from a different thread 
# than the one that created it. FastAPI can handle a single request across multiple threads (for example, dependencies and endpoints running in a threadpool), so without this flag you'd hit ProgrammingError: SQLite objects created in a thread can only be used in that same thread.
# Setting it to False turns that check off.

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

