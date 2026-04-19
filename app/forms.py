from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, Email, Optional, NumberRange

class RegisterForm(FlaskForm):
    username = StringField("아이디", validators=[DataRequired(), Length(min=3, max=30)])
    email = StringField("이메일", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("비밀번호", validators=[DataRequired(), Length(min=8, max=72)])
    confirm_password = PasswordField("비밀번호 확인", validators=[DataRequired(), EqualTo("password")])
    grade = SelectField("학년", choices=[("1", "1학년"), ("2", "2학년"), ("3", "3학년")], validators=[DataRequired()])
    submit = SubmitField("회원가입")

class LoginForm(FlaskForm):
    username = StringField("아이디", validators=[DataRequired()])
    password = PasswordField("비밀번호", validators=[DataRequired()])
    submit = SubmitField("로그인")

class PostForm(FlaskForm):
    board = SelectField("게시판", choices=[("all", "전체게시판"), ("1", "1학년"), ("2", "2학년"), ("3", "3학년")], validators=[DataRequired()])
    category = SelectField("말머리", choices=[("notice", "공지"), ("free", "자유"), ("question", "질문"), ("study", "공부"), ("file", "자료")], validators=[DataRequired()])
    title = StringField("제목", validators=[DataRequired(), Length(min=2, max=200)])
    content = TextAreaField("본문", validators=[DataRequired(), Length(min=2, max=10000)])
    submit = SubmitField("저장")

class CommentForm(FlaskForm):
    content = TextAreaField("댓글", validators=[DataRequired(), Length(min=1, max=2000)])
    parent_id = IntegerField("parent_id", validators=[Optional(), NumberRange(min=1)])
    submit = SubmitField("등록")

class ReportForm(FlaskForm):
    reason = SelectField("사유", choices=[("spam", "도배"), ("abuse", "욕설/괴롭힘"), ("nsfw", "부적절한 첨부"), ("ads", "광고/홍보"), ("other", "기타")], validators=[DataRequired()])
    detail = TextAreaField("상세", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("신고")

class BanForm(FlaskForm):
    target_user_id = IntegerField("사용자 ID", validators=[DataRequired(), NumberRange(min=1)])
    ban_type = SelectField("제재유형", choices=[("full", "영구/기간 이용정지"), ("read_only", "읽기전용 제한")], validators=[DataRequired()])
    days = IntegerField("기간(일, 비우면 영구)", validators=[Optional(), NumberRange(min=1, max=3650)])
    reason = SelectField("사유", choices=[("abuse", "욕설/괴롭힘"), ("spam", "도배"), ("nsfw", "부적절 콘텐츠"), ("ads", "광고/홍보"), ("other", "기타")], validators=[DataRequired()])
    note = TextAreaField("메모", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("적용")

class IPBanForm(FlaskForm):
    ip_address = StringField("IP", validators=[DataRequired(), Length(min=7, max=64)])
    days = IntegerField("기간(일, 비우면 영구)", validators=[Optional(), NumberRange(min=1, max=3650)])
    reason = StringField("사유", validators=[DataRequired(), Length(max=100)])
    note = TextAreaField("메모", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("IP 밴 적용")