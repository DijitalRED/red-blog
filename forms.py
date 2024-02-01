from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField, SelectField, RadioField
# from wtforms.fields.simple import EmailField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


class CreatePostForm(FlaskForm):
    title = StringField("Başlık", validators=[DataRequired()])
    subtitle = StringField("Alt Başlık", validators=[DataRequired()])
    img_url = StringField("Resim Linki", validators=[DataRequired(), URL()])
    body = CKEditorField("İçerik", validators=[DataRequired()])
    submit = SubmitField("Yayınla")


class RegisterForm(FlaskForm):
    name = StringField("İsim", validators=[DataRequired()])
    email = EmailField("E-Posta", validators=[DataRequired()])
    password = PasswordField("Şifre", validators=[DataRequired()])
    submit = SubmitField("Kayıt Ol")


class LoginForm(FlaskForm):
    email = StringField("E-Posta", validators=[DataRequired()])
    password = PasswordField("Şifre", validators=[DataRequired()])
    submit = SubmitField("Giriş Yap")


class CommentForm(FlaskForm):
    comment = CKEditorField("Yorum", validators=[DataRequired()])
    submit = SubmitField("Gönder")


class ContactForm(FlaskForm):
    name = StringField("İsminiz", validators=[DataRequired()])
    email = StringField("E-Posta Adresiniz", validators=[DataRequired()])
    phone = StringField("Telefon Numaranız", validators=[DataRequired()])
    message = CKEditorField("Mesajınız", validators=[DataRequired()])
    submit = SubmitField("Gönder")


class AdminForm(FlaskForm):
    the_user = SelectField("Kullanıcı Seçin", validators=[DataRequired()])
    submit = SubmitField("Ekle/Kaldır")

    def __init__(self, users):
        super(AdminForm, self).__init__()
        the_users = [(user.id, f"{user.name} ({user.email})") for user in users if user.id != 1]
        self.the_user.choices = the_users
