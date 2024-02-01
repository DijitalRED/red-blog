import smtplib
from email.header import Header
from email.mime.text import MIMEText

from flask import Flask, abort, render_template, redirect, url_for, flash, request, get_flashed_messages
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey, Boolean
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm, ContactForm, AdminForm
from datetime import date
import os

FROM_ADDRESS = os.environ.get('MAIL_ADDRESS')
FROM_ADDRESS_PASSWORD = os.environ.get('MAIL_PASSWORD')
TO_ADDRESS = "dijitalrediletisim@gmail.com"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)

login_manager = LoginManager(app)
login_manager.init_app(app)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///blog.db")
db = SQLAlchemy(model_class=Base)
db.init_app(app)

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


# CONFIGURE TABLES
class User(UserMixin, db.Model):
    __tablename__ = "users"

    def __init__(self, email, password, name, is_admin):
        self.email = email
        self.password = password
        self.name = name
        self.is_admin = is_admin

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)

    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False)

    blogposts: Mapped[list["BlogPost"]] = relationship(back_populates="author")
    comments: Mapped[list["Comment"]] = relationship(back_populates="author")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    # author: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    author: Mapped["User"] = relationship(back_populates="blogposts")

    comments: Mapped[list["Comment"]] = relationship(back_populates="post")


class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)

    post_id: Mapped[int] = mapped_column(ForeignKey("blog_posts.id"))
    post: Mapped["BlogPost"] = relationship(back_populates="comments")

    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    author: Mapped["User"] = relationship(back_populates="comments")


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.context_processor
def now():
    return {'date': date}


def admin_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(current_user.is_admin)
        if current_user.id != 1 and not current_user.is_admin:
            return abort(403)
        return func(*args, **kwargs)

    return wrapper


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        check_user = db.session.execute(db.select(User).where(User.email == request.form["email"])).scalar()
        if not check_user:
            user = User(
                email=request.form["email"],
                password=generate_password_hash(request.form["password"], "pbkdf2:sha256", 8),
                name=request.form["name"],
                is_admin=False
            )
            db.session.add(user)
            db.session.commit()

            login_user(user)
            return redirect(url_for('get_all_posts'))
        else:
            flash("Zaten bu e-posta ile hesap oluşturulmuş, giriş yapın!")
            return redirect(url_for('login'))
    return render_template("register.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():

        user = db.session.execute(db.select(User).where(User.email == request.form["email"])).scalar()
        if user:
            if check_password_hash(user.password, request.form["password"]):
                login_user(user)
                return redirect(url_for("get_all_posts"))
            else:
                error = "Şifre yanlış, lütfen tekrar deneyin."
        else:
            error = "Bu e-posta adresi ile bağlantılı bir hesap bulunamadı, lütfen tekrar deneyin."
    else:
        error = get_flashed_messages()
        if error:
            if list == type(error):
                error = error[0]
    return render_template("login.html", form=form, error=error)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts)


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    form = CommentForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            comment = Comment(
                text=request.form["comment"],

                post_id=post_id,
                post=requested_post,

                author_id=current_user.id,
                author=current_user,
            )
            db.session.add(comment)
            db.session.commit()
        else:
            flash("Log in to post a comment.")
            return redirect(url_for('login'))
    return render_template("post.html", post=requested_post, form=form)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            author_id=current_user.id,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    if current_user.id == post.author.id:
        edit_form = CreatePostForm(
            title=post.title,
            subtitle=post.subtitle,
            img_url=post.img_url,
            author=post.author,
            author_id=db.Column(db.Integer, db.ForeignKey("users.id")),
            body=post.body
        )
        if edit_form.validate_on_submit():
            post.title = edit_form.title.data
            post.subtitle = edit_form.subtitle.data
            post.img_url = edit_form.img_url.data
            post.author = current_user
            post.author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
            post.body = edit_form.body.data
            db.session.commit()
            return redirect(url_for("show_post", post_id=post.id))
        return render_template("make-post.html", form=edit_form, is_edit=True)
    else:
        return abort(403)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")


def send_mail(subject, body, to_address):
    msg = MIMEText(body, _charset="UTF-8")
    msg['Subject'] = Header(subject, "utf-8")
    with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
        connection.starttls()
        connection.login(user=FROM_ADDRESS, password=FROM_ADDRESS_PASSWORD)
        connection.sendmail(
            from_addr=FROM_ADDRESS,
            to_addrs=to_address,
            msg=msg.as_string()
        )


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if current_user.is_authenticated:
        form = ContactForm(
            name=current_user.name,
            email=current_user.email
        )
    else:
        form = ContactForm()

    if request.method == "POST":
        body = (f"{request.form['message']}\n\nGönderen: {request.form['name']}\n\nE-Posta: {request.form['email']}\n"
                f"Telefon Numarası: {request.form['phone']}")
        try:
            send_mail(subject="Blog Feedback", body=body, to_address=TO_ADDRESS)
        except smtplib.SMTPException:
            title = "Bir şeyler ters gitti. Mesajın gönderilemedi."
        else:
            title = "Mesajın başarıyla gönderildi."
    else:
        title = "İletişim"
    return render_template("contact.html", title=title, form=form)


@app.route("/admin/add", methods=["GET", "POST"])
@admin_only
def admin_add():
    if current_user.id == 1:
        result = db.session.execute(db.select(User))
        users = result.scalars().all()
        form = AdminForm(users)
        if form.validate_on_submit():
            the_id = int(request.form["the_user"])
            the_user = db.get_or_404(User, the_id)
            the_user.is_admin = True
            db.session.commit()
        return render_template("admin.html", form=form)
    else:
        return abort(404)


@app.route("/admin/remove", methods=["GET", "POST"])
@admin_only
def admin_remove():
    if current_user.id == 1:
        result = db.session.execute(db.select(User))
        users = result.scalars().all()
        form = AdminForm(users)
        if form.validate_on_submit():
            the_id = int(request.form["the_user"])
            the_user = db.get_or_404(User, the_id)
            the_user.is_admin = False
            db.session.commit()
        return render_template("admin.html", form=form)
    else:
        return abort(404)


@app.route("/admins", methods=["GET"])
@admin_only
def admins():
    if current_user.id == 1:
        result = db.session.execute(db.select(User))
        users = result.scalars().all()
        return render_template("admins.html", users=users)
    else:
        return abort(404)


if __name__ == "__main__":
    app.run(debug=False)
