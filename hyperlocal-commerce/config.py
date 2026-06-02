import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Application configuration.

    Defaults to a local SQLite database so the project runs with zero setup
    (perfect for a hackathon demo). To use MySQL instead, set the DATABASE_URL
    environment variable, e.g.:

        export DATABASE_URL="mysql+pymysql://user:pass@localhost/hyperlocal"

    A ready-to-import MySQL schema is provided in schema_mysql.sql.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "hyperlocal-dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "hyperlocal.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Public Google Maps JS API key (used by the frontend). Optional: the UI
    # gracefully falls back to a lightweight Leaflet/OpenStreetMap map when this
    # is empty, so the demo works offline / without a key.
    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")

    # Default "customer" location used when the browser blocks geolocation.
    # (Bengaluru city centre — matches the seeded sample stores.)
    DEFAULT_LAT = 12.9716
    DEFAULT_LNG = 77.5946
