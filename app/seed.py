from .models import User
from . import db

def seed_admin():
    admin = User.query.filter_by(username="admin").first()
    if admin:
        return

    admin = User(
        username="admin",
        email="jayoon0127@gmail.com",
        grade=1,
        role="superadmin",
    )
    admin.set_password("3$141592@pi")
    db.session.add(admin)
    db.session.commit()