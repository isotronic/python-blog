from flask import Flask, render_template, request
import requests
import smtplib
import os

MY_EMAIL = os.environ["EMAIL"]
MY_PASSWORD = os.environ["PASSWORD"]

blog_data = requests.get("https://api.npoint.io/6ec16c82a70a7636c5f2").json()

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html", blog_posts=blog_data)


@app.route("/contact", methods=["POST", "GET"])
def contact():
    if request.method == "POST":
        heading = "Message successfully sent"
        with smtplib.SMTP("smtp.gmail.com") as connection:
            connection.starttls()
            connection.login(user=MY_EMAIL, password=MY_PASSWORD)
            connection.sendmail(
                from_addr=MY_EMAIL,
                to_addrs=MY_EMAIL,
                msg=f"Subject: New Contact Form Entry - Joseph's Blog\n\n"
                    f"Name: {request.form['name']}\n"
                    f"Email: {request.form['email']}\n"
                    f"Phone: {request.form['phone']}\n"
                    f"Message: {request.form['message']}"
            )
    else:
        heading = "Contact"

    return render_template("contact.html", heading=heading)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/post/<post_id>")
def single_post(post_id):
    post = [post for post in blog_data if post["id"] == int(post_id)]
    return render_template("post.html", post=post[0])


if __name__ == "__main__":
    app.run(debug=True)
