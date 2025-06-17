from tut import db, User
from werkzeug.security import generate_password_hash
import json

def init_database():
    # Create all database tables
    db.create_all()
    
    # Load config
    with open('config.json', 'r') as c:
        params = json.load(c)["params"]
    
    # Check if admin user already exists
    admin_user = User.query.filter_by(email=params['admin_user']).first()
    if not admin_user:
        # Create admin user
        admin = User(
            email=params['admin_user'],
            password=generate_password_hash(params['admin_password'])
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")
    else:
        print("Admin user already exists!")

if __name__ == "__main__":
    init_database() 