from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import config

engine = create_async_engine(url=config.database_url, echo=False)
Session = async_sessionmaker(bind=engine, autoflush=False)
