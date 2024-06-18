from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Role, User

passw = "p!32Mz?Wt59X~[kC"
url = f'postgresql://OpenAgriDBUser:{passw}@/openagri?host=localhost'
engine = create_engine(url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()


def init_roles():
    existing_roles = db.query(Role).all()
    if len(existing_roles) > 0:
        return

    admin_role = Role(name="Admin")
    user_role = Role(name="User")

    db.add_all([admin_role, user_role])
    db.commit()


def init_admin_user():
    admin_role = db.query(Role).filter(Role.name == "Admin").first()
    pwd_context = CryptContext(schemes=["argon2"])
    password_hashed = pwd_context.hash("Windows8")
    basic_admin = User(email="stefan.drobic@vizlore.com", password=password_hashed, role_id=admin_role.id)

    db.add(basic_admin)
    db.commit()


def init_db():
    init_roles()
    init_admin_user()
    db.flush()
    db.close()


if __name__ == "__main__":
    init_db()
