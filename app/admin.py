from datetime import timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from . import db
from .forms import BanForm, IPBanForm
from .models import User, Post, Report, Ban, IPBan, now_utc

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.before_request
def admin_required():
    if not current_user.is_authenticated or not current_user.is_admin():
        abort(403)

@admin_bp.route("/")
@login_required
def dashboard():
    return render_template(
        "admin_dashboard.html",
        reports=Report.query.order_by(Report.created_at.desc()).limit(30).all(),
        users=User.query.order_by(User.created_at.desc()).limit(30).all(),
        posts=Post.query.order_by(Post.created_at.desc()).limit(30).all(),
        bans=Ban.query.order_by(Ban.created_at.desc()).limit(30).all(),
        ip_bans=IPBan.query.order_by(IPBan.created_at.desc()).limit(30).all(),
        ban_form=BanForm(),
        ip_ban_form=IPBanForm(),
    )

@admin_bp.route("/ban", methods=["POST"])
@login_required
def ban_user():
    form = BanForm()
    if form.validate_on_submit():
        ends_at = now_utc() + timedelta(days=form.days.data) if form.days.data else None
        db.session.add(Ban(
            user_id=form.target_user_id.data,
            ban_type=form.ban_type.data,
            reason=form.reason.data,
            note=form.note.data,
            ends_at=ends_at,
            created_by=current_user.id,
        ))
        db.session.commit()
        flash("사용자 제재가 적용되었습니다.", "success")
    else:
        flash("입력값을 확인하세요.", "danger")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/ip-ban", methods=["POST"])
@login_required
def ip_ban():
    form = IPBanForm()
    if form.validate_on_submit():
        ends_at = now_utc() + timedelta(days=form.days.data) if form.days.data else None
        db.session.add(IPBan(
            ip_address=form.ip_address.data.strip(),
            reason=form.reason.data.strip(),
            note=form.note.data,
            ends_at=ends_at,
            created_by=current_user.id,
        ))
        db.session.commit()
        flash("IP 밴이 적용되었습니다.", "success")
    else:
        flash("입력값을 확인하세요.", "danger")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/posts/<int:post_id>/pin", methods=["POST"])
@login_required
def pin_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.is_pinned = not post.is_pinned
    db.session.commit()
    flash("고정 상태가 변경되었습니다.", "success")
    return redirect(request.referrer or url_for("admin.dashboard"))

@admin_bp.route("/posts/<int:post_id>/hide", methods=["POST"])
@login_required
def hide_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.is_hidden = not post.is_hidden
    db.session.commit()
    flash("숨김 상태가 변경되었습니다.", "success")
    return redirect(request.referrer or url_for("admin.dashboard"))

@admin_bp.route("/posts/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post_admin(post_id):
    post = Post.query.get_or_404(post_id)
    post.is_deleted = True
    db.session.commit()
    flash("관리자에 의해 게시글이 삭제되었습니다.", "success")
    return redirect(request.referrer or url_for("admin.dashboard"))

@admin_bp.route("/reports/<int:report_id>/resolve", methods=["POST"])
@login_required
def resolve_report(report_id):
    report = Report.query.get_or_404(report_id)
    report.status = "resolved"
    report.handled_by = current_user.id
    report.handled_at = now_utc()
    db.session.commit()
    flash("신고가 처리되었습니다.", "success")
    return redirect(url_for("admin.dashboard"))