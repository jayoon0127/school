import os
from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    upload_dir = os.getenv(
        "UPLOAD_DIR",
        os.path.join(app.root_path, "static", "uploads")
    )

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "change-this-to-a-long-random-secret"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///school_board.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=int(os.getenv("MAX_CONTENT_LENGTH", 10 * 1024 * 1024)),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("FLASK_ENV", "development") != "development",
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_SECURE=os.getenv("FLASK_ENV", "development") != "development",
        WTF_CSRF_TIME_LIMIT=7200,
        UPLOAD_DIR=upload_dir,
    )

    os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)

    if os.getenv("TRUST_PROXY", "0") == "1":
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    os.makedirs(os.path.join(app.root_path, "static", app.config["UPLOAD_DIR"]), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "로그인이 필요합니다."

    from .models import User, Ban, IPBan

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.before_request
    def protect_requests():
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()
        if ip:
            blocked = IPBan.active_for_ip(ip)
            if blocked:
                abort(403, description="접속이 제한된 IP입니다.")

        from flask_login import current_user
        if current_user.is_authenticated:
            active_ban = Ban.active_for_user(current_user.id)
            if active_ban and active_ban.ban_type == "full":
                abort(403, description="계정 이용이 정지되었습니다.")

    from .auth import auth_bp
    from .board import board_bp
    from .admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(board_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()
        from .seed import seed_admin
        seed_admin()

    return app