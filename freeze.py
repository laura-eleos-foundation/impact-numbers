# freeze.py
from flask_frozen import Freezer
from main import app # Import your Flask app

freezer = Freezer(app)

if __name__ == '__main__':
    freezer.freeze()