import os
import smtplib
from flask import Flask, render_template, redirect, url_for, flash, abort, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
from functools import wraps


gmail_user = os.environ.get('EMAIL')
password_one = os.environ.get('PASSWORD')


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
uri = os.getenv("DATABASE_URL", "sqlite:///blog.db")  # or other relevant config var
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = f"{uri}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

gravatar = Gravatar(app,
                    size=100,
                    rating="g",
                    default="retro",
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


##CONFIGURE TABLES

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(100))
    password = db.Column(db.String(100))

    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comments", back_populates="comment_author")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = relationship("User", back_populates="posts")

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    comments = relationship("Comments", back_populates="parent_post")


class Comments(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comment_author = relationship("User", back_populates="comments")

    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    text = db.Column(db.Text, nullable=False)


with app.app_context():
    db.create_all()


def admin_only(f):
    @wraps(f)
    def decoration_fun(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id not in (1, 2):
            return abort(403)
        return f(*args, **kwargs)
    return decoration_fun


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def hello():
    return render_template('index.html')


@app.route('/portfolio')
def port():
    return render_template('portfolio.html')


@app.route('/sv')
def sv_one():
    style = 'style.scc'
    score = 0
    return render_template('index_main.html', style=style, sc=score)

# /////////////////////////////////////////


@app.route('/main')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("blog/index.html", all_posts=posts, logg_in=current_user.is_authenticated)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user_email = form.email.data
        if User.query.filter_by(email=user_email).first():
            flash("You have already had email just log in!")
            return redirect(url_for('login'))
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            password=generate_password_hash(password=form.password.data, method="pbkdf2:sha256", salt_length=8)
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("get_all_posts"))
    return render_template("blog/register.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_email = form.email.data
        user = User.query.filter_by(email=user_email).first()
        if not user:
            flash("Invalid Email please try again! ")
            return redirect(url_for("login"))
        if not check_password_hash(user.password, form.password.data):
            flash("Invalid password try again!")
            return redirect(url_for("login"))
        else:
            login_user(user)
            return redirect(url_for("get_all_posts"))
    return render_template("blog/login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    form = CommentForm()
    requested_post = BlogPost.query.get(post_id)

    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for('login'))
        new_comment = Comments(
            text=form.comment.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template("blog/post.html", post=requested_post, form=form, current_user=current_user,
                           logg_in=current_user.is_authenticated)


@app.route("/about")
def about():
    return render_template("blog/about.html", logg_in=current_user.is_authenticated)


@app.route("/contact.html", methods=['GET', 'POST'])
def contact_it():
    if request.method == 'POST':
        data_for_it = request.form
        with smtplib.SMTP("SMTP.mail.ru") as data_sms:
            data_sms.starttls()
            data_sms.login(gmail_user, password_one)
            data_sms.sendmail(from_addr=gmail_user,
                              to_addrs="asanbekovmaksat@yahoo.com",
                              msg=f"Subject: Email from {data_for_it['name']}\n\n{data_for_it['message']}\n"
                                  f"Email: {data_for_it['email']}\nPhone: {data_for_it['phone']} ")
        return render_template("blog/contact.html", msg_sent=True, logg_in=current_user.is_authenticated)
    else:
        return render_template("blog/contact.html", msg_sent=False, logg_in=current_user.is_authenticated)


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
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("blog/make-post.html", form=form, logg_in=current_user.is_authenticated)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("blog/make-post.html", form=edit_form, logg_in=current_user.is_authenticated)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == '__main__':
    app.run(debug=True, port=8000)

