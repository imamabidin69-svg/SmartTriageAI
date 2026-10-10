"""Titik masuk aplikasi untuk server WSGI, misalnya: gunicorn run:app"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
