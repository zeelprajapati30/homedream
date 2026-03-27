from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "dreamhome_secret"

# ==============================
# DATABASE CONFIG
# ==============================

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/home_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==============================
# MODELS
# ==============================

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def first_name(self):
        """Get first name from full name"""
        return self.name.split()[0] if self.name else ""
    
    @property
    def last_name(self):
        """Get last name from full name"""
        parts = self.name.split()
        return parts[-1] if len(parts) > 1 else ""


class Architect(db.Model):
    __tablename__ = "architects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    experience = db.Column(db.Integer)
    specialization = db.Column(db.String(150))
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Project(db.Model):
    
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    location = db.Column(db.String(150))
    price = db.Column(db.Float)
    architect_id = db.Column(db.Integer, db.ForeignKey("architects.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    images = db.relationship("ProjectImage", backref="project", lazy=True)


class ProjectImage(db.Model):
    __tablename__ = "project_images"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    booking_date = db.Column(db.Date)
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    rating = db.Column(db.Integer)
    review = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SavedDesign(db.Model):
    __tablename__ = "saved_designs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(150))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class NewsletterSubscriber(db.Model):
    __tablename__ = "newsletter_subscribers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)


# ==============================
# ROUTES
# ==============================

@app.route("/")
def home_redirect():
    if "user_id" in session:
        return redirect(url_for("index"))  # ✅ now works
    return redirect(url_for("signin"))

    projects = Project.query.all()
    architects = Architect.query.all()
    reviews = Review.query.order_by(Review.created_at.desc()).limit(6).all()

    return render_template("index.html", projects=projects, architects=architects, reviews=reviews)

@app.route("/home")
def index():
    if "user_id" not in session:
        return redirect(url_for("signin"))

    projects = Project.query.all()
    architects = Architect.query.all()
    reviews = Review.query.order_by(Review.created_at.desc()).limit(6).all()

    return render_template("index.html", projects=projects, architects=architects, reviews=reviews)

# Projects routes - both names for compatibility
@app.route("/projects")
def projects():
    if "user_id" not in session:
        return redirect(url_for("signin"))

    projects = Project.query.all()
    return render_template("projects.html", projects=projects)


@app.route("/projects-page")
def projects_page():
    if "user_id" not in session:
        return redirect(url_for("signin"))

    return projects()


@app.route("/architecture")
def architecture_page():
    if "user_id" not in session:
        return redirect(url_for("signin"))

    architects = Architect.query.all()
    return render_template("architecture.html", architects=architects)


@app.route("/about")
def about_page():
    if "user_id" not in session:
        return redirect(url_for("signin"))

    return render_template("about.html")


@app.route("/reviews")
def reviews_page():
    if "user_id" not in session:
        return redirect(url_for("signin"))

    reviews = Review.query.order_by(Review.created_at.desc()).all()
    projects = Project.query.all()

    return render_template("reviews.html", reviews=reviews, projects=projects)


@app.route("/contact")
def contact_page():
    if "user_id" not in session:
        return redirect(url_for("signin"))

    return render_template("contact.html")


@app.route("/book-now")
def book_now():
    if "user_id" not in session:
        return redirect(url_for("signin"))

    projects = Project.query.all()
    return render_template("book-now.html", projects=projects)


@app.route("/project/<int:id>")
def project_detail_page(id):
    if "user_id" not in session:
        return redirect(url_for("signin"))

    project = Project.query.get_or_404(id)
    images = ProjectImage.query.filter_by(project_id=id).all()

    return render_template("project-detail.html", project=project, images=images)


# ==============================
# AUTHENTICATION
# ==============================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Get form data
        first_name = request.form.get("first_name", "")
        last_name = request.form.get("last_name", "")
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        # Validation
        if not all([first_name, last_name, email, password, confirm_password]):
            flash("All fields are required", "danger")
            return render_template("register.html")
        
        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return render_template("register.html")
        
        if len(password) < 6:
            flash("Password must be at least 6 characters long", "danger")
            return render_template("register.html")
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for("signin"))
        
        # Create new user
        full_name = f"{first_name} {last_name}".strip()
        user = User(
            name=full_name,
            email=email,
            phone="",  # Phone not in register form, set to empty string
            password=generate_password_hash(password)
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("signin"))
        except Exception as e:
            db.session.rollback()
            flash("Registration failed. Please try again.", "danger")
            return render_template("register.html")
    
    return render_template("register.html")


# Alias for auth_register to match template
@app.route("/auth/register", methods=["POST"])
def auth_register():
    # Get form data
    first_name = request.form.get("first_name", "")
    last_name = request.form.get("last_name", "")
    email = request.form.get("email", "")
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")
    
    # Validation
    if not all([first_name, last_name, email, password, confirm_password]):
        flash("All fields are required", "danger")
        return redirect(url_for("register"))
    
    if password != confirm_password:
        flash("Passwords do not match", "danger")
        return redirect(url_for("register"))
    
    if len(password) < 6:
        flash("Password must be at least 6 characters long", "danger")
        return redirect(url_for("register"))
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash("Email already registered. Please login.", "warning")
        return redirect(url_for("signin"))
    
    # Create new user
    full_name = f"{first_name} {last_name}".strip()
    user = User(
        name=full_name,
        email=email,
        phone="",  # Phone not in register form, set to empty string
        password=generate_password_hash(password)
    )
    
    try:
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("signin"))
    except Exception as e:
        db.session.rollback()
        flash("Registration failed. Please try again.", "danger")
        return redirect(url_for("register"))


@app.route("/signin", methods=["GET", "POST"])
def signin():
    # If user is already logged in, redirect to dashboard
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        
        if not email or not password:
            flash("Email and password are required", "danger")
            return render_template("signin.html")
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            # Set session
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_email"] = user.email
            session.permanent = True  # Make session permanent
            
            flash(f"Welcome back, {user.first_name}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password", "danger")
            return render_template("signin.html")
    
    return render_template("signin.html")


@app.route("/auth/signin", methods=["POST"])
def auth_signin():
    email = request.form.get("email", "")
    password = request.form.get("password", "")
    
    if not email or not password:
        flash("Email and password are required", "danger")
        return redirect(url_for("signin"))
    
    user = User.query.filter_by(email=email).first()
    
    if user and check_password_hash(user.password, password):
        # Set session
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_email"] = user.email
        session.permanent = True  # Make session permanent
        
        flash(f"Welcome back, {user.first_name}!", "success")
        return redirect(url_for("dashboard"))
    else:
        flash("Invalid email or password", "danger")
        return redirect(url_for("signin"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully", "info")
    return redirect(url_for("index"))


# ==============================
# DASHBOARD
# ==============================

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("signin"))

    user = User.query.get(session["user_id"])

    if not user:
        session.clear()
        return redirect(url_for("signin"))

    saved_designs = SavedDesign.query.filter_by(user_id=session["user_id"]).all()
    bookings = Booking.query.filter_by(user_id=session["user_id"]).all()

    stats = {
        'total_bookings': len(bookings),
        'confirmed_bookings': len([b for b in bookings if b.status == 'confirmed']),
        'pending_bookings': len([b for b in bookings if b.status == 'pending']),
        'total_saved': len(saved_designs)
    }

    return render_template("dashboard.html", user=user, bookings=bookings, stats=stats)
    
    # Create a user object with properties for the template
    class TemplateUser:
        def __init__(self, db_user):
            self.id = db_user.id
            self.name = db_user.name
            self.email = db_user.email
            self.phone = db_user.phone
            self.created_at = db_user.created_at
            self.username = db_user.email.split('@')[0]  # Create username from email
            self.is_admin = False  # Default to False
            
            # Split name for first_name and last_name
            name_parts = db_user.name.split() if db_user.name else ["", ""]
            self.first_name = name_parts[0] if len(name_parts) > 0 else ""
            self.last_name = name_parts[-1] if len(name_parts) > 1 else ""
    
    template_user = TemplateUser(user)
    
    # Pass datetime to template
    return render_template("dashboard.html", 
                          user=template_user, 
                          bookings=bookings, 
                          stats=stats,
                          datetime=datetime)


# ==============================
# BOOKING
# ==============================

@app.route("/book", methods=["POST"])
def book():

    if "user_id" not in session:
        flash("Please login to book a project", "warning")
        return redirect(url_for("signin"))

    booking = Booking(
        user_id=session.get("user_id"),
        project_id=request.form["project_id"],
        booking_date=datetime.strptime(request.form["date"], "%Y-%m-%d").date()
    )

    db.session.add(booking)
    db.session.commit()

    flash("Booking successful!", "success")

    return redirect(url_for("dashboard"))


# ==============================
# CONTACT
# ==============================

@app.route("/contact/submit", methods=["POST"])
def contact_submit():

    name = request.form["name"]
    email = request.form["email"]
    message = request.form["message"]

    contact = ContactMessage(
        name=name,
        email=email,
        message=message
    )

    db.session.add(contact)
    db.session.commit()

    flash("Thank you for contacting us!", "success")
    return redirect(url_for("contact_page"))


# ==============================
# NEWSLETTER
# ==============================

@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form["email"]
    
    # Check if already subscribed
    existing = NewsletterSubscriber.query.filter_by(email=email).first()
    if existing:
        return jsonify({"status": "already_subscribed"})
    
    sub = NewsletterSubscriber(email=email)
    db.session.add(sub)
    db.session.commit()
    return jsonify({"status": "subscribed"})

@app.route("/submit-review", methods=["POST"])
def submit_review():

    if "user_id" not in session:
        flash("Please login to submit review", "warning")
        return redirect(url_for("signin"))

    review = Review(
        user_id=session["user_id"],
        project_id=request.form["project_id"],
        rating=int(request.form["rating"]),
        review=request.form["review"]
    )

    db.session.add(review)
    db.session.commit()

    flash("Review submitted successfully!", "success")

    return redirect(url_for("reviews_page"))
# ==============================
# CONTEXT PROCESSOR
# ==============================

@app.context_processor
def utility_processor():
    return dict(datetime=datetime)


# ==============================
# START APP
# ==============================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Database connected successfully")
        print("✅ Tables verified")
        print("✅ Registration and Login flow ready")
    app.run(debug=True)