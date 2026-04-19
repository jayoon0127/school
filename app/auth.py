from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from .forms import RegisterForm, LoginForm
from .models import User
from . import db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("board.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data.strip()).first():
            flash("이미 사용 중인 아이디입니다.", "danger")
            return render_template("register.html", form=form)

        if User.query.filter_by(email=form.email.data.strip().lower()).first():
            flash("이미 사용 중인 이메일입니다.", "danger")
            return render_template("register.html", form=form)

        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            grade=int(form.grade.data),
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("회원가입 완료. 로그인하세요.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("board.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user and user.check_password(form.password.data) and user.is_active_user:
            login_user(user, remember=True)
            flash("로그인되었습니다.", "success")
            return redirect(url_for("board.index"))

        flash("아이디 또는 비밀번호가 올바르지 않습니다.", "danger")

    return render_template("login.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("로그아웃되었습니다.", "success")
    return redirect(url_for("auth.login"))