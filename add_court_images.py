#!/usr/bin/env python3
"""
Add demo images to courts for testing
"""
from app import create_app
from models.court import Court
from models.database import db
import json

def add_demo_images():
    app = create_app()
    with app.app_context():
        courts = Court.query.all()
        
        # Demo tennis court images (free stock photos)
        demo_images = [
            "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400",
            "https://images.unsplash.com/photo-1622279457486-62dcc4a431d6?w=400",
            "https://images.unsplash.com/photo-1544717925-c973e4f3e6ce?w=400",
            "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=400",
            "https://images.unsplash.com/photo-1520778869159-0a88c017e8b0?w=400"
        ]
        
        for i, court in enumerate(courts):
            image_url = demo_images[i % len(demo_images)]
            court.image_urls = json.dumps([image_url])
        
        db.session.commit()
        print(f"Added demo images to {len(courts)} courts")

if __name__ == '__main__':
    add_demo_images()