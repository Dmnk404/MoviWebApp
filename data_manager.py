from models import db, User, Movie, UserMovie

class DataManager:
    def __init__(self):
        self.db = db

    # -----------------------------
    # Commit-Hilfsmethode
    # -----------------------------
    def _commit(self):
        """Tries to commit changes to database."""
        try:
            self.db.session.commit()
        except Exception as e:
            self.db.session.rollback()
            raise e

    # -----------------------------
    # Hilfsfunktionen
    # -----------------------------
    def _get_user(self, user_id: int) -> User:
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"Kein User mit der ID {user_id} gefunden.")
        return user

    def _get_user_by_name(self, username: str) -> User | None:
        return User.query.filter_by(username=username).first()

    def _get_or_create_movie(self, movie: Movie) -> Movie:
        existing_movie = Movie.query.filter_by(
            title=movie.title,
            director=movie.director,
            year=movie.year
        ).first()
        if existing_movie:
            return existing_movie
        self.db.session.add(movie)
        self._commit()
        return movie

    def _get_user_movie(self, user_id: int, movie_id: int, create_if_missing: bool = False) -> UserMovie | None:
        user_movie = UserMovie.query.filter_by(user_id=user_id, movie_id=movie_id).first()
        if not user_movie and create_if_missing:
            user_movie = UserMovie(user_id=user_id, movie_id=movie_id)
            self.db.session.add(user_movie)
            self._commit()
        return user_movie

    # -----------------------------
    # User-Funktionen
    # -----------------------------
    def get_users(self):
        users = User.query.all()
        return users if users else []

    def create_user(self, name: str):
        if not name or not name.strip():
            raise ValueError("Username can't be empty.")
        if len(name) > 80:
            raise ValueError("Username too long.")

        if self._get_user_by_name(name):
            raise ValueError(f"The username '{name}' already exists.")

        new_user = User(username=name)
        self.db.session.add(new_user)
        self._commit()
        return new_user

    def edit_user(self, name: str, new_name: str):
        user = self._get_user_by_name(name)
        if not user:
            return False
        user.username = new_name
        self._commit()
        return True

    def delete_user(self, name: str):
        user = self._get_user_by_name(name)
        if not user:
            return False
        self.db.session.delete(user)
        self._commit()
        return True

    # -----------------------------
    # Movie-Funktionen
    # -----------------------------
    def get_movies(self, user_id: int):
        movies = (
            Movie.query
            .join(UserMovie)
            .filter(UserMovie.user_id == user_id)
            .add_columns(UserMovie.comment)  # Kommentar direkt mit abfragen
            .all()
        )
        return movies if movies else []

    def add_movie(self, user_id: int, movie: Movie):
        user = self._get_user(user_id)
        movie_to_use = self._get_or_create_movie(movie)
        self._get_user_movie(user.id, movie_to_use.id, create_if_missing=True)
        return movie_to_use

    def set_comment(self, user_id: int, movie_id: int, comment: str):
        user_movie = self._get_user_movie(user_id, movie_id, create_if_missing=True)
        user_movie.comment = comment
        self._commit()
        return user_movie

    def delete_user_movie(self, user_id: int, movie_id: int):
        user_movie = self._get_user_movie(user_id, movie_id)
        if not user_movie:
            raise ValueError(f"Keine Verknüpfung zwischen User {user_id} und Movie {movie_id} gefunden.")
        self.db.session.delete(user_movie)
        self._commit()
