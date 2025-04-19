from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    age = Column(Integer)
    gender = Column(String)
    
    # İlişki tanımlaması
    watch_history = relationship("WatchHistory", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")

class Movie(Base):
    __tablename__ = 'movies'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    genre = Column(String)
    release_year = Column(Integer)
    
    # İlişki tanımlaması
    watch_history = relationship("WatchHistory", back_populates="movie")
    recommendations = relationship("Recommendation", back_populates="movie")

class WatchHistory(Base):
    __tablename__ = 'watch_history'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    movie_id = Column(Integer, ForeignKey('movies.id'))
    watch_date = Column(DateTime, default=datetime.utcnow)
    rating = Column(Float, nullable=True)  # Opsiyonel puan
    
    # İlişki tanımlamaları
    user = relationship("User", back_populates="watch_history")
    movie = relationship("Movie", back_populates="watch_history") 

class Recommendation(Base):
    __tablename__ = 'recommendations'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    movie_id = Column(Integer, ForeignKey('movies.id'))
    score = Column(Float)  # Öneri puanı/skoru
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # İlişki tanımlamaları
    user = relationship("User", back_populates="recommendations")
    movie = relationship("Movie", back_populates="recommendations")