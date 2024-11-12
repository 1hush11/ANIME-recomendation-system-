from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors

# Подготовка данных и создание разряженной матрицы
df_sample = pd.read_csv('Data_anime_sample.csv')
pivot_table = df_sample.pivot_table(
    index='user_id',
    columns='name',
    values='user rating',
).fillna(0)

# Перевёрнутая таблица (аниме в строках)
pivot_table_T = pivot_table.T

# Вычисление косинусного сходства
similarity_score = cosine_similarity(pivot_table.T)

# Инициализация модели для KNN
sparse_matrix = csr_matrix(pivot_table.values)
model_knn = NearestNeighbors(metric='cosine', algorithm='brute')
model_knn.fit(sparse_matrix)

# Функция для рекомендаций на основе косинусного сходства
def cos_recommend_anime(anime_name, n_recommendations_cos):
    try:
        index = np.where(pivot_table_T.index == anime_name)[0][0]
    except IndexError:
        print(f"'{anime_name}' не найдено.")
        return []

    similar_anime = sorted(
        list(enumerate(similarity_score[index])),
        key=lambda x: x[1],
        reverse=True
    )[1:n_recommendations_cos + 1]

    data = []
    for i in similar_anime:
        item = []
        temp_df = df_sample[df_sample['name'] == pivot_table_T.index[i[0]]]
        if not temp_df.empty:
            item.extend(list(temp_df.drop_duplicates('name')['name'].values))
            data.append(item)
        else:
            print(f"Данные для аниме с индексом {i[0]} не найдены.")
    return data


# Функция для рекомендаций на основе модели KNN
def get_recommendations(anime_name, n_recommendations=10):
    if anime_name not in pivot_table.columns:
        raise ValueError(f"Аниме '{anime_name}' не найдено.")

    anime_index = pivot_table.columns.get_loc(anime_name)
    anime_vector = sparse_matrix[anime_index, :].toarray().reshape(1, -1)

    distances, indices = model_knn.kneighbors(anime_vector, n_neighbors=n_recommendations + 1)

    recommendations = [
        {"anime": pivot_table.columns[idx], "distance": distances.flatten()[i]}
        for i, idx in enumerate(indices.flatten()[1:], start=1)
        if idx < len(pivot_table.columns)
    ]
    return recommendations


# Функция для рекомендаций по жанру
def recommend_by_genre(genre_name, top_n=10):
    genre_df = df_sample[df_sample['genre'].str.contains(genre_name, case=False, na=False)]

    if genre_df.empty:
        print(f"Нет аниме с жанром '{genre_name}'.")
        return []

    # Удаление дубликатов названий и сортировка по рейтингу
    top_anime_by_genre = genre_df.drop_duplicates(subset='name').sort_values(by='rating', ascending=False).head(top_n)

    # Создание списка с названиями
    recommendations = list(top_anime_by_genre['name'].values)

    return recommendations

app = FastAPI()

# Модель для запроса
class RecommendationRequest(BaseModel):
    anime_name: str
    n_recommendations: int = 10

# API-метод для получения рекомендаций по KNN
@app.post("/recommendations/")
def recommend(request: RecommendationRequest):
    try:
        recommendations = get_recommendations(request.anime_name, request.n_recommendations)
        return {"recommendations": recommendations}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Модель для запроса для косинусного сходства
class CosineRecommendationRequest(BaseModel):
    anime_name: str
    n_recommendations_cos: int = 10

# API-метод для получения рекомендаций по косинусному сходству
@app.post("/cos_recommendations/")
def cos_recommend(request: CosineRecommendationRequest):
    try:
        recommendations = cos_recommend_anime(request.anime_name, n_recommendations_cos=request.n_recommendations_cos)
        if recommendations:
            return {"recommendations": recommendations}
        else:
            raise HTTPException(status_code=404, detail=f"Не удалось найти рекомендации для '{request.anime_name}'")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Модель для запроса для рекомендаций по жанру
class GenreRecommendationRequest(BaseModel):
    genre_name: str
    top_n: int = 10

# API-метод для получения рекомендаций по жанру
@app.post("/genre_recommendations/")
async def genre_recommend(request: GenreRecommendationRequest):
    recommendations = recommend_by_genre(request.genre_name, request.top_n)
    if recommendations:
        return {"recommendations": recommendations}
    else:
        raise HTTPException(status_code=404, detail=f"Не удалось найти аниме с жанром '{request.genre_name}'")

# API-метод для получения топ-10 аниме
@app.post("/top_anime/")
async def get_top_anime():
    top_rated_anime = df_sample.sort_values(by='rating', ascending=False)
    unique_anime_titles = top_rated_anime.drop_duplicates(subset='name')[['name', 'rating']].to_dict(orient="records")[1:11]
    if unique_anime_titles:
        return {"unique_anime_titles": unique_anime_titles}
    else:
        raise HTTPException(status_code=404, detail="Не удалось найти топ аниме")
