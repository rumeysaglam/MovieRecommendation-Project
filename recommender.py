import pandas as pd
from sklearn.cluster import KMeans
from sqlalchemy.orm import Session
from typing import List, Dict
import numpy as np
from models import WatchHistory

class MovieRecommender:
    def __init__(self, n_clusters: int = 5):
        self.n_clusters = n_clusters
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        self.user_clusters = None
        self.genre_vectors = None
        
    def prepare_data(self, db: Session) -> pd.DataFrame:
        """Veritabanından verileri çekip pandas DataFrame'e dönüştürür"""
        # Tüm izleme geçmişini çek
        watch_history = db.query(WatchHistory).all()
        
        # Verileri DataFrame'e dönüştür
        data = []
        for watch in watch_history:
            data.append({
                'user_id': watch.user_id,
                'movie_id': watch.movie_id,
                'genre': watch.movie.genre,
                'rating': watch.rating if watch.rating else 0
            })
        
        return pd.DataFrame(data)
    
    def create_genre_vectors(self, df: pd.DataFrame) -> Dict[int, np.ndarray]:
        """Her kullanıcı için tür bazlı tercih vektörleri oluşturur"""
        # Tüm benzersiz türleri bul
        all_genres = set()
        for genres in df['genre'].unique():
            all_genres.update(genres.split(','))
        
        # Her kullanıcı için tür vektörü oluştur
        user_vectors = {}
        for user_id in df['user_id'].unique():
            user_df = df[df['user_id'] == user_id]
            vector = np.zeros(len(all_genres))
            
            for _, row in user_df.iterrows():
                genres = row['genre'].split(',')
                rating = row['rating']
                for genre in genres:
                    if genre in all_genres:
                        idx = list(all_genres).index(genre)
                        vector[idx] += rating
            
            user_vectors[user_id] = vector
        
        return user_vectors
    
    def fit(self, db: Session):
        """Modeli eğitir"""
        df = self.prepare_data(db)
        self.genre_vectors = self.create_genre_vectors(df)
        
        # Kullanıcı vektörlerini numpy array'e dönüştür
        X = np.array(list(self.genre_vectors.values()))
        
        # KMeans ile kümeleme yap
        self.kmeans.fit(X)
        self.user_clusters = dict(zip(self.genre_vectors.keys(), self.kmeans.labels_))
    
    def recommend_movies(self, db: Session, user_id: int, n_recommendations: int = 5) -> List[int]:
        """Belirli bir kullanıcı için film önerileri yapar"""
        if user_id not in self.user_clusters:
            return []
        
        # Kullanıcının kümesini bul
        user_cluster = self.user_clusters[user_id]
        
        # Aynı kümedeki diğer kullanıcıları bul
        similar_users = [uid for uid, cluster in self.user_clusters.items() 
                        if cluster == user_cluster and uid != user_id]
        
        # Kullanıcının izlediği filmleri bul
        watched_movies = set(wh.movie_id for wh in db.query(WatchHistory)
                           .filter(WatchHistory.user_id == user_id))
        
        # Benzer kullanıcıların izlediği ama hedef kullanıcının izlemediği filmleri bul
        recommended_movies = []
        for similar_user in similar_users:
            user_movies = set(wh.movie_id for wh in db.query(WatchHistory)
                            .filter(WatchHistory.user_id == int(similar_user)))
            new_movies = user_movies - watched_movies
            recommended_movies.extend(new_movies)
        
        # En çok önerilen filmleri döndür
        movie_counts = {}
        for movie_id in recommended_movies:
            movie_counts[movie_id] = movie_counts.get(movie_id, 0) + 1
        
        return sorted(movie_counts.keys(), 
                     key=lambda x: movie_counts[x], 
                     reverse=True)[:n_recommendations] 