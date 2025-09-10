#!/usr/bin/env bash
pip install --upgrade pip
pip install -r requirements.txt

python -c "
from app import create_app
from models.database import db
import os
os.environ['FLASK_ENV'] = 'production'
app = create_app()
with app.app_context():
    db.create_all()
    print('Database initialized!')
"