from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from db.connection import *
from helpers.directory import *
from helpers.fileUploadRestrictions import *
from helpers.passwordPolicies import *

app = Flask(__name__)

# strong secret key => prevent brute-forcing & cookies attacks
app.config["SECRET_KEY"] = "sahdgjkshgdjkhsakjdhkasjhdkj"

# rate limiter =>
# to prevent brute-forcing attack on specific routes that
# attacker can attack on it
limiter = Limiter(
    get_remote_address, app=app, default_limits=["150 per day", "70 per hour"]
)


@app.route("/")
def home():
    if "username" in session:
        user_id = session["user_id"]
        return render_template("index.html", username=session["username"])
    flash("You're not logged in!")
    return redirect(url_for("login"))


@app.route("/login", methods=["POST", "GET"])
@limiter.limit("5 per minute")
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        username = request.form["username"]
        password = request.form["password"]

        user = get_user_by_username(username)

        if user:
            if is_password_matched(password, user[3]):
                session["username"] = user[1]
                session["user_id"] = user[0]
                return redirect(url_for("home"))

        flash("Invalid Credentials!", "danger")
        return render_template("login.html")


@app.route("/sign-up", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form["username"]
        password = request.form["password1"]
        email = request.form["email"]
        confirmPassword = request.form["password2"]

        user = get_user_by_username(username)

        if user:
            flash("Username already exists!", "danger")
            return render_template("register.html")

        if password != confirmPassword:
            flash("Password doesn't match!!", "warning")
            return render_template("register.html")

        if check_password_policies(password):
            add_user(username, password, email)
            flash("Username is registered Successfully!", "success")
        else:
            flash("Your password is weak try another strong one!", "warning")
            return render_template("register.html")

    return redirect(url_for("login"))


@app.route("/upload-note", methods=["GET", "POST"])
def UploadNote():
    if request.method == "POST":
        category = request.form["category"]
        image = request.files["image"]
        content = request.form["content"]
        user_id = session["user_id"]

        if image:
            if not allowed_file_size(image) or not allowed_file_extension(
                image.filename
            ):
                flash("Invalid Image uploaded!!", "danger")
                return render_template("UploadNote.html")

            image_url = f"uploads/{image.filename}"
            image.save(f"static/{image_url}")

            add_note(user_id, category, content, image_url)

            flash("Your Note Uploaded Successfully ", "success")

            return redirect(url_for("MyNotes"))

        add_note(user_id, category, content)

        flash("Your Note Uploaded Successfully ", "success")

        return redirect(url_for("MyNotes"))
    else:
        if not "user_id" in session:
            flash("Please Login to do this action", "danger")
            return redirect(url_for("login"))
    return render_template("UploadNote.html")


@app.route("/my-notes")
def MyNotes():
    if "user_id" in session:
        return render_template("notes.html", notes=get_all_notes(session["user_id"]))
    flash("You're not logged in!")
    return redirect(url_for("login"))





@app.route("/search", methods=["GET","POST"])
def search():
    #if  "user_id" in session:
    if request.method == "POST":
        title=request.form["job_name"]
        user_id=session["user_id"]
        return render_template("notes.html",notes=get_note_by_titel(user_id,title))
        #return render_template("notes.html", notes=get_all_notes(user_id))

    else:    
        if not "user_id" in session:
            return redirect(url_for("login"))
        return redirect(url_for("home"))

        #return render_template("notes.html", notes=get_all_notes(session["user_id"]))
    

            






@app.route("/plans")
def PlansPage():
    if "username" in session:
        return render_template("plans.html", plans=get_all_plans())
    flash("You're not logged in!")
    return redirect(url_for("login"))


@app.route("/admin/add-new-plan", methods=["POST", "GET"])
def AddNewPlan():
    if session["username"] == "admin" and session["user_id"] == 1:
        if request.method == "POST":
            title = request.form["title"]
            price = request.form["price"]
            description = request.form["description"]

            add_plan(title, price, description)

            flash("New plan Added Successfully!", "success")
            return render_template("add_plan.html")

        return render_template("add_plan.html")

    flash("You're not allowed to take this action!")
    return redirect(url_for("home"))


if __name__ == "__main__":
    if not is_directory_exist("static/uploads"):
        create_directory("static/uploads")
    init_db()
    create_admin()
    app.run(debug=True)
