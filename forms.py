from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TelField, TextAreaField, HiddenField, PasswordField
from wtforms.validators import DataRequired, URL, Email
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post
class NewPostForm(FlaskForm):
    title = StringField(label="Post Title", validators=[DataRequired()])
    subtitle = StringField(label="Subtitle", validators=[DataRequired()])
    img_url = StringField(label="Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField(label="Post Body", validators=[DataRequired()])
    post_id = HiddenField()
    submit = SubmitField(label="Submit Post")


class ContactForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired()])
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    phone = TelField(label="Phone", validators=[DataRequired()])
    message = TextAreaField(label="Message", validators=[DataRequired()])
    submit = SubmitField(label="Send")


class RegisterForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired()])
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    submit = SubmitField(label="Register")


class LoginForm(FlaskForm):
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    password = PasswordField(label="Password", validators=[DataRequired()])
    submit = SubmitField(label="Login")


# TODO: Create a CommentForm so users can leave comments below posts
