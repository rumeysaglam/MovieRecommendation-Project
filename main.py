from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models import User, Movie, WatchHistory
from recommender import MovieRecommender

app = FastAPI(title="Netflix Film Öneri Sistemi")

# Pydantic modelleri
class UserCreate(BaseModel):
    username: str
    email: str
    age: int
    gender: str

class MovieCreate(BaseModel):
    title: str
    genre: str
    release_year: int

class WatchHistoryCreate(BaseModel):
    user_id: int
    movie_id: int
    rating: float = None

# Kullanıcı işlemleri
@app.post("/users/", response_model=UserCreate)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/{user_id}", response_model=UserCreate)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Film işlemleri
@app.post("/movies/", response_model=MovieCreate)
def create_movie(movie: MovieCreate, db: Session = Depends(get_db)):
    db_movie = Movie(**movie.dict())
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie

@app.get("/movies/{movie_id}", response_model=MovieCreate)
def read_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

# İzleme geçmişi işlemleri
@app.post("/watch/", response_model=WatchHistoryCreate)
def add_watch_history(watch: WatchHistoryCreate, db: Session = Depends(get_db)):
    db_watch = WatchHistory(**watch.dict())
    db.add(db_watch)
    db.commit()
    db.refresh(db_watch)
    return db_watch

@app.get("/users/{user_id}/watch_history")
def get_user_watch_history(user_id: int, db: Session = Depends(get_db)):
    history = db.query(WatchHistory).filter(WatchHistory.user_id == user_id).all()
    return history

# Öneri sistemi
recommender = MovieRecommender()

@app.get("/recommend/{user_id}")
def get_recommendations(user_id: int, db: Session = Depends(get_db)):
    # Modeli güncelle
    recommender.fit(db)
    
    # Önerileri al
    recommended_movie_ids = recommender.recommend_movies(db, user_id)
    
    # Film detaylarını getir
    recommended_movies = []
    for movie_id in recommended_movie_ids:
        movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if movie:
            recommended_movies.append({
                "id": movie.id,
                "title": movie.title,
                "genre": movie.genre,
                "release_year": movie.release_year
            })
    
    return {"recommendations": recommended_movies}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 