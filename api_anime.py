import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

# Функция для получения топа аниме
def get_top_anime():
    try:
        response = requests.post(f"{API_URL}/top_anime/")
        response.raise_for_status()
        top_anime = response.json().get("unique_anime_titles", [])
        return top_anime
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка запроса: {e}")
        return []


# Функция для получения рекомендаций по косинусному сходству
def get_cos_recommendations(anime_name, n_recommendations_cos):
    response = requests.post(f"{API_URL}/cos_recommendations/", json={
        "anime_name": anime_name,
        "n_recommendations_cos": n_recommendations_cos
    })

    if response.status_code == 200:
        return response.json()["recommendations"]
    else:
        st.error(f"Ошибка: {response.json()['detail']}")
        return []


# Функция для получения рекомендаций по KNN
def get_knn_recommendations(anime_name):
    response = requests.post(f"{API_URL}/recommendations/", json={
        "anime_name": anime_name,
        "n_recommendations": 18
    })

    if response.status_code == 200:
        return response.json()["recommendations"]
    else:
        st.error(f"Ошибка: {response.json()['detail']}")
        return []


# Функция для получения рекомендаций по жанру
def get_genre_recommendations(genre_name, top_n):
    response = requests.post(f"{API_URL}/genre_recommendations/", json={
        "genre_name": genre_name,
        "top_n": top_n
    })

    if response.status_code == 200:
        return response.json()["recommendations"]
    else:
        st.error(f"Ошибка: {response.json()['detail']}")
        return []



# Streamlit интерфейс
st.title('Рекомендательная система для аниме')

# Топ аниме
st.header('Топ-10 аниме')

# Кнопка для загрузки топа аниме
if st.button("Показать топ аниме"):
    top_anime = get_top_anime()
    if top_anime:
        st.write("Топ аниме:")
        for idx, anime in enumerate(top_anime, start=1):
            st.write(f"{idx}. {anime['name']} (рейтинг: {anime['rating']})")

# Рекомендации по косинусному сходству
st.header('Рекомендации по косинусному сходству')

# Ввод названия аниме для рекомендаций по сходству
anime_name_cos = st.text_input("Введите название аниме для рекомендаций по сходству:")

# Ввод количества рекомендаций по косинусному сходству
n_recommendations_cos = st.slider("Количество рекомендаций по сходству", min_value=1, max_value=20, value=10)

# Получить рекомендации по косинусному сходству
if anime_name_cos:
    recommendations_cos = get_cos_recommendations(anime_name_cos, n_recommendations_cos)
    if recommendations_cos:
        st.write(f"Рекомендации по сходству для аниме '{anime_name_cos}':")
        for rec in recommendations_cos:
            st.write(f"- {rec[0]}")


# Рекомендации по KNN
st.header('Рекомендации по KNN')

# Ввод названия аниме для рекомендаций по KNN
anime_name_knn = st.text_input("Введите название аниме для рекомендаций по KNN:")

# Получить рекомендации по KNN
if anime_name_knn:
    recommendations_knn = get_knn_recommendations(anime_name_knn)
    if recommendations_knn:
        st.write(f"Рекомендации для аниме '{anime_name_knn}':")
        for idx, rec in enumerate(recommendations_knn, 1):
            st.write(f"{idx}. {rec['anime']}")


# Рекомендации по жанру
st.header('Рекомендации по жанру')

# Ввод жанра для рекомендаций
genre_name = st.text_input("Введите жанр для рекомендаций:")

# Ввод количества рекомендаций по жанру
top_n_genre = st.slider("Количество рекомендаций по жанру", min_value=1, max_value=20, value=10)

# Получить рекомендации по жанру
if genre_name:
    recommendations_genre = get_genre_recommendations(genre_name, top_n_genre)
    if recommendations_genre:
        st.write(f"Рекомендации для жанра '{genre_name}':")
        for idx, rec in enumerate(recommendations_genre, 1):
            st.write(f"{idx}. {rec}")

st.write("## API-методы:")
st.write("1. **Топ-10 аниме**: Метод для получения 10 лучших аниме по рейтингу.")
st.write("2. **Косинусное сходство**: Возвращает список похожих аниме на основе косинусного сходства выбранного количества.")
st.write("3. **Рекомендаци по KNN**: Возвращает список аниме, похожих на указанное.")
st.write("4. **Рекомендации по жанру**: Возвращает лучшие аниме по указанному жанру на основе косинусного"
                                                            " сходства такого количества, сколько выбрали.")

