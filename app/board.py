from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import or_
from .forms import PostForm, CommentForm, ReportForm
from .models import db, User, Post, Attachment, Reaction, Comment, Report, Notification, Ban
from .utils import sanitize_html, save_upload

board_bp = Blueprint("board", __name__)

def can_write(user):
    active_ban = Ban.active_for_user(user.id)
    if not active_ban:
        return True
    return active_ban.ban_type != "read_only"

def notify(user_id, kind, message, link=None):
    db.session.add(Notification(user_id=user_id, kind=kind, message=message, link=link))

@board_bp.route("/")
@login_required
def index():
    board = request.args.get("board", "all")
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "hot")

    posts = Post.query.filter_by(is_deleted=False, is_hidden=False)

    if board in {"1", "2", "3"}:
        posts = posts.filter_by(board=board)

    if q:
        posts = posts.join(User, Post.author_id == User.id).filter(
            or_(
                Post.title.ilike(f"%{q}%"),
                Post.content.ilike(f"%{q}%"),
                User.username.ilike(f"%{q}%")
            )
        )

    if sort == "latest":
        posts = posts.order_by(Post.is_pinned.desc(), Post.created_at.desc())
    elif sort == "comments":
        posts = posts.order_by(Post.is_pinned.desc(), Post.comment_count.desc(), Post.created_at.desc())
    else:
        posts = posts.order_by(Post.is_pinned.desc(), Post.hot_score.desc(), Post.created_at.desc())

    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(10).all()

    return render_template("index.html", posts=posts.limit(50).all(), board=board, q=q, sort=sort, notifications=notifications)

@board_bp.route("/posts/new", methods=["GET", "POST"])
@login_required
def create_post():
    if not can_write(current_user):
        abort(403, description="읽기 전용 제한 상태입니다.")

    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            board=form.board.data,
            category=form.category.data,
            title=form.title.data.strip(),
            content=sanitize_html(form.content.data),
            author_id=current_user.id,
        )
        db.session.add(post)
        db.session.flush()

        for uploaded in request.files.getlist("attachments"):
            if uploaded and uploaded.filename:
                meta = save_upload(uploaded)
                if meta:
                    db.session.add(Attachment(post_id=post.id, **meta))

        post.recalc_hot_score()
        db.session.commit()
        flash("게시글이 등록되었습니다.", "success")
        return redirect(url_for("board.post_detail", post_id=post.id))

    return render_template("post_form.html", form=form, post=None)

@board_bp.route("/posts/<int:post_id>")
@login_required
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    if post.is_deleted or post.is_hidden:
        abort(404)

    post.view_count += 1
    post.recalc_hot_score()
    db.session.commit()

    comments = Comment.query.filter_by(post_id=post.id).order_by(Comment.created_at.asc()).all()
    return render_template("post_detail.html", post=post, comments=comments, comment_form=CommentForm(), report_form=ReportForm())

@board_bp.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author_id != current_user.id and not current_user.is_admin():
        abort(403)

    form = PostForm(obj=post)
    if form.validate_on_submit():
        post.board = form.board.data
        post.category = form.category.data
        post.title = form.title.data.strip()
        post.content = sanitize_html(form.content.data)
        db.session.commit()
        flash("게시글이 수정되었습니다.", "success")
        return redirect(url_for("board.post_detail", post_id=post.id))

    return render_template("post_form.html", form=form, post=post)

@board_bp.route("/posts/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author_id != current_user.id and not current_user.is_admin():
        abort(403)

    post.is_deleted = True
    db.session.commit()
    flash("게시글이 삭제되었습니다.", "success")
    return redirect(url_for("board.index"))

@board_bp.route("/posts/<int:post_id>/reaction/<kind>", methods=["POST"])
@login_required
def react(post_id, kind):
    if kind not in {"like", "dislike"}:
        abort(400)

    post = Post.query.get_or_404(post_id)
    reaction = Reaction.query.filter_by(post_id=post.id, user_id=current_user.id).first()

    if reaction and reaction.reaction_type == kind:
        db.session.delete(reaction)
    else:
        if reaction:
            reaction.reaction_type = kind
        else:
            db.session.add(Reaction(post_id=post.id, user_id=current_user.id, reaction_type=kind))

    db.session.flush()
    post.like_count = Reaction.query.filter_by(post_id=post.id, reaction_type="like").count()
    post.dislike_count = Reaction.query.filter_by(post_id=post.id, reaction_type="dislike").count()
    post.recalc_hot_score()

    if post.author_id != current_user.id and kind == "like":
        notify(post.author_id, "post_like", f"'{post.title}' 글에 좋아요가 눌렸습니다.", url_for("board.post_detail", post_id=post.id))

    db.session.commit()
    return redirect(url_for("board.post_detail", post_id=post.id))

@board_bp.route("/posts/<int:post_id>/comments", methods=["POST"])
@login_required
def create_comment(post_id):
    if not can_write(current_user):
        abort(403, description="읽기 전용 제한 상태입니다.")

    post = Post.query.get_or_404(post_id)
    form = CommentForm()

    if form.validate_on_submit():
        comment = Comment(
            post_id=post.id,
            author_id=current_user.id,
            parent_id=form.parent_id.data,
            content=sanitize_html(form.content.data),
        )
        db.session.add(comment)
        db.session.flush()

        post.comment_count = Comment.query.filter_by(post_id=post.id, is_deleted=False).count()
        post.recalc_hot_score()

        if comment.parent_id:
            parent = Comment.query.get(comment.parent_id)
            if parent and parent.author_id != current_user.id:
                notify(parent.author_id, "reply", "내 댓글에 답글이 달렸습니다.", url_for("board.post_detail", post_id=post.id))
        elif post.author_id != current_user.id:
            notify(post.author_id, "comment", f"'{post.title}' 글에 댓글이 달렸습니다.", url_for("board.post_detail", post_id=post.id))

        db.session.commit()
        flash("댓글이 등록되었습니다.", "success")

    return redirect(url_for("board.post_detail", post_id=post.id))

@board_bp.route("/comments/<int:comment_id>/edit", methods=["POST"])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.author_id != current_user.id and not current_user.is_admin():
        abort(403)

    content = request.form.get("content", "").strip()
    if not content:
        abort(400)

    comment.content = sanitize_html(content)
    db.session.commit()
    flash("댓글이 수정되었습니다.", "success")
    return redirect(url_for("board.post_detail", post_id=comment.post_id))

@board_bp.route("/comments/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.author_id != current_user.id and not current_user.is_admin():
        abort(403)

    comment.is_deleted = True
    comment.content = "삭제된 댓글입니다."

    post = Post.query.get(comment.post_id)
    post.comment_count = Comment.query.filter_by(post_id=post.id, is_deleted=False).count()
    post.recalc_hot_score()

    db.session.commit()
    flash("댓글이 삭제되었습니다.", "success")
    return redirect(url_for("board.post_detail", post_id=comment.post_id))

@board_bp.route("/posts/<int:post_id>/report", methods=["POST"])
@login_required
def report_post(post_id):
    form = ReportForm()
    post = Post.query.get_or_404(post_id)

    if form.validate_on_submit():
        db.session.add(Report(
            reporter_id=current_user.id,
            target_type="post",
            target_post_id=post.id,
            reason=form.reason.data,
            detail=form.detail.data,
        ))
        db.session.commit()
        flash("신고가 접수되었습니다.", "success")

    return redirect(url_for("board.post_detail", post_id=post.id))

@board_bp.route("/comments/<int:comment_id>/report", methods=["POST"])
@login_required
def report_comment(comment_id):
    form = ReportForm()
    comment = Comment.query.get_or_404(comment_id)

    if form.validate_on_submit():
        db.session.add(Report(
            reporter_id=current_user.id,
            target_type="comment",
            target_comment_id=comment.id,
            reason=form.reason.data,
            detail=form.detail.data,
        ))
        db.session.commit()
        flash("신고가 접수되었습니다.", "success")

    return redirect(url_for("board.post_detail", post_id=comment.post_id))