import os

SECRET_KEY = os.urandom(12).hex()
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database
SQLALCHEMY_TRACK_MODIFICATIONS = False

# TODO IMPLEMENT DATABASE URL
SQLALCHEMY_DATABASE_URI = (
    "postgresql+psycopg2://postgres:goodness4321@localhost/fyyur_app"
)
