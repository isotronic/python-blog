from flask import Flask, render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TelField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Email, URL
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor, CKEditorField
from datetime import date
import smtplib
import os


class ContactForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired()])
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    phone = TelField(label="Phone", validators=[DataRequired()])
    message = TextAreaField(label="Message", validators=[DataRequired()])
    submit = SubmitField(label="Send")


class NewPostForm(FlaskForm):
    title = StringField(label="Post Title", validators=[DataRequired()])
    subtitle = StringField(label="Subtitle", validators=[DataRequired()])
    author = StringField(label="Author's Name", validators=[DataRequired()])
    img_url = StringField(label="Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField(label="Post Body", validators=[DataRequired()])
    post_id = HiddenField()
    submit = SubmitField(label="Submit Post")


MY_EMAIL = os.environ["EMAIL"]
MY_PASSWORD = os.environ["PASSWORD"]

app = Flask(__name__)
app.secret_key = "some-secret-string"

bootstrap = Bootstrap5(app)
ckeditor = CKEditor(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy()
db.init_app(app)


# CONFIGURE TABLE
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    with app.app_context():
        result = db.session.execute(db.select(BlogPost)).scalars().all()
    posts = [post.to_dict() for post in result]
    return render_template("index.html", blog_posts=posts)


@app.route("/post/<post_id>")
def single_post(post_id):
    with app.app_context():
        post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar()
    return render_template("post.html", post=post)


@app.route("/new-post", methods=["POST", "GET"])
def new_post():
    form = NewPostForm()
    heading = "New Post"
    if form.validate_on_submit():
        post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            date=date.today().strftime("%B %d, %Y"),
            body=form.body.data,
            author=form.author.data,
            img_url=form.img_url.data
        )
        with app.app_context():
            db.session.add(post)
            db.session.commit()
        return redirect(url_for("home"))
    return render_template("make-post.html", form=form, heading=heading)


@app.route("/edit-post/<post_id>", methods=["POST", "GET"])
def edit_post(post_id):
    with app.app_context():
        post = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar()
    form = NewPostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body,
        post_id=post_id
    )
    if form.validate_on_submit():
        with app.app_context():
            post_to_edit = db.session.execute(db.select(BlogPost).where(BlogPost.id == form.post_id.data)).scalar()
            post_to_edit.title = form.title.data
            post_to_edit.subtitle = form.subtitle.data
            post_to_edit.body = form.body.data
            post_to_edit.author = form.author.data
            post_to_edit.img_url = form.author.data
            db.session.commit()
        return redirect(url_for("single_post", post_id=form.post_id.data))
    heading = "Edit Post"
    return render_template("make-post.html", form=form, heading=heading)


@app.route("/delete/<post_id>")
def delete_post(post_id):
    with app.app_context():
        post_to_delete = db.session.execute(db.select(BlogPost).where(BlogPost.id == post_id)).scalar()
        db.session.delete(post_to_delete)
        db.session.commit()
    return redirect(url_for("home"))


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


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True, port=5003)
