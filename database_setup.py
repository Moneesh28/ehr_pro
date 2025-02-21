from flask import Flask
from models import db, User, bcrypt  # Import bcrypt from models

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ehr_users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def setup_database():
    with app.app_context():  # Ensure we're inside the application context
        db.drop_all()  # Drop existing tables
        db.create_all()  # Create fresh tables
        
        # Create sample users with properly hashed passwords
        users = [
            User("patient1", "password123", "patient"),
            User("doctor1", "password123", "doctor"),
            User("nurse1", "password123", "nurse"),
            User("admin1", "password123", "admin"),
        ]
        
        db.session.bulk_save_objects(users)  # Add multiple users efficiently
        db.session.commit()
        print("Database setup complete!")

if __name__ == "__main__":
    setup_database()
