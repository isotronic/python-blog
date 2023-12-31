from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap5
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_ckeditor import CKEditor
from datetime import date
from forms import ContactForm, NewPostForm, RegisterForm, LoginForm, CommentForm
import smtplib
import os

# Get email and password from environment variables
MY_EMAIL = os.environ["EMAIL"]
MY_PASSWORD = os.environ["PASSWORD"]

# Initialize Flask app and configure settings
app = Flask(__name__)
app.secret_key = "some-secret-string"

# Initialize Bootstrap and CKEditor extensions
bootstrap = Bootstrap5(app)
ckeditor = CKEditor(app)

# Initialize LoginManager for user authentication
login_manager = LoginManager()
login_manager.init_app(app)

# Configure the SQLAlchemy database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
db = SQLAlchemy()
db.init_app(app)

# Initialize Gravatar for user profile images
gravatar = Gravatar(app, rating="g", default="retro",
                    force_default=False, force_lower=False, use_ssl=True, base_url=None)


# Define the BlogPost class to represent blog posts in the database
class BlogPost(db.Model):
    # Table name and columns
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.relationship("User", back_populates="posts")
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    img_url = db.Column(db.String(250), nullable=False)
    comments = db.relationship("Comment", back_populates="parent_post")

    # Convert the object to a dictionary
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# Define the User class for user authentication and authorship
class User(db.Model, UserMixin):
    # Table name and columns
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)
    name = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    posts = db.relationship("BlogPost", back_populates="author")
    comments = db.relationship("Comment", back_populates="author")


# Define the Comment class for blog post comments
class Comment(db.Model):
    # Table name and columns
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    author = db.relationship("User", back_populates="comments")
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = db.relationship("BlogPost", back_populates="comments")


# Create database tables within the app context
with app.app_context():
    db.create_all()


# Load the user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Custom decorator to restrict access to admin-only routes
def admin_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.id == 1:  # Assuming admin user ID is 1
            return abort(403)  # Return Forbidden status
        return func(*args, **kwargs)
    return decorated_function


# Route for the home page
@app.route("/")
def home():
    result = db.session.execute(db.select(BlogPost)).scalars().all()
    return render_template("index.html", blog_posts=result)


# Route for user registration
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.data.get("name")
        email = form.data.get("email")

        # Check if user already exists
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user:
            flash("That email is already registered with us. Try logging in instead.")
            return redirect(url_for("login"))

        # Hash the password and create a new user
        hashed_password = generate_password_hash(form.data.get("password"))
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # Log in the new user
        login_user(new_user)

        return redirect(url_for("home"))
    return render_template("register.html", form=form)


# Route for user login
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.data.get("email")
        password = form.data.get("password")

        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))
        else:
            flash("Login details are incorrect. Please try again.")

    return render_template("login.html", form=form)


# Route for user logout
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


# Route for viewing a single blog post
@app.route("/post/<post_id>", methods=["GET", "POST"])
def single_post(post_id):
    form = CommentForm()
    if form.validate_on_submit():
        # Create a new comment and add it to the database
        comment = Comment(
            text=form.data.get("comment"),
            author_id=current_user.id,
            post_id=post_id
        )
        with app.app_context():
            db.session.add(comment)
            db.session.commit()

    # Retrieve the specified blog post
    post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar()
    return render_template("post.html", post=post, form=form)


# Route for creating a new blog post (admin-only)
@app.route("/new-post", methods=["POST", "GET"])
@admin_required
def new_post():
    form = NewPostForm()
    heading = "New Post"
    if form.validate_on_submit():
        # Create a new blog post and add it to the database
        post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            date=date.today().strftime("%B %d, %Y"),
            body=form.body.data,
            author_id=current_user.id,
            img_url=form.img_url.data
        )
        with app.app_context():
            db.session.add(post)
            db.session.commit()
        return redirect(url_for("home"))
    return render_template("make-post.html", form=form, heading=heading)


# Route for editing an existing blog post (admin-only)
@app.route("/edit-post/<post_id>", methods=["POST", "GET"])
@admin_required
def edit_post(post_id):
    post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar()
    form = NewPostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body,
        post_id=post_id
    )
    if form.validate_on_submit():
        # Update the blog post in the database
        post_to_edit = db.session.execute(db.select(BlogPost).where(BlogPost.id == form.post_id.data)).scalar()
        post_to_edit.title = form.title.data
        post_to_edit.subtitle = form.subtitle.data
        post_to_edit.body = form.body.data
        post_to_edit.img_url = form.img_url.data
        db.session.commit()
        return redirect(url_for("single_post", post_id=form.post_id.data))
    heading = "Edit Post"
    return render_template("make-post.html", form=form, heading=heading)


# Route for deleting a blog post (admin-only)
@app.route("/delete/<int:post_id>")
@admin_required
def delete_post(post_id):
    post_to_delete = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar()
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


# Route for the contact page
@app.route("/contact", methods=["POST", "GET"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        heading = "Message successfully sent"
        with smtplib.SMTP("smtp.gmail.com") as connection:
            connection.starttls()
            connection.login(user=MY_EMAIL, password=MY_PASSWORD)
            connection.sendmail(
                from_addr=MY_EMAIL,
                to_addrs=MY_EMAIL,
                msg=f"Subject: New Contact Form Entry - Joseph's Blog\n\n"
                    f"Name: {form.name.data}\n"
                    f"Email: {form.email.data}\n"
                    f"Phone: {form.phone.data}\n"
                    f"Message: {form.message.data}"
            )
    else:
        heading = "Contact"

    return render_template("contact.html", heading=heading, form=form)


# Route for the about page
@app.route("/about")
def about():
    return render_template("about.html")


# Run the app in debug mode if executed directly
if __name__ == "__main__":
    app.run(debug=True, port=5003)
