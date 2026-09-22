# ✅ Flask and SQLAlchemy imports
from flask import Flask, render_template, url_for, request, redirect, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename  # For secure file names
# ✅ Date and Time Imports (Only importing `datetime` class once)
from datetime import datetime, timedelta

# ✅ Background Scheduler
from apscheduler.schedulers.background import BackgroundScheduler

# ✅ ReportLab for PDF generation
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

# ✅ Other necessary modules
import os
import time
import random
import smtplib
from email.mime.text import MIMEText
import mysql.connector
from flask import jsonify







# Initialize Flask App
app = Flask(__name__)
app.secret_key = os.urandom(24)

# MySQL Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@localhost/hotel_project'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=3)

# Initialize Database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# -----------------------
# Database Models
# -----------------------

class User(db.Model):
    __tablename__ = 'user'  # Ensure table name consistency
    id = db.Column(db.Integer, primary_key=True)
    
    # ✅ Login credentials
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    
    # ✅ Profile details
    fname = db.Column(db.String(50), nullable=True)
    lname = db.Column(db.String(50), nullable=True)
    contact = db.Column(db.String(15), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    address = db.Column(db.Text, nullable=True)
    gender = db.Column(db.Enum('Male', 'Female', 'Other'), nullable=True)
    profile_image = db.Column(db.String(255), nullable=True)

    # ✅ Admin & Profile completion fields
    is_admin = db.Column(db.Boolean, default=False)  
    profile_complete = db.Column(db.Boolean, default=False)  # Added profile completion field

    # ✅ Timestamps
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # ✅ Password Hashing Methods
    def set_password(self, password):
        """ Hash the password before storing it """
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """ Verify password hash """
        return check_password_hash(self.password, password)
# ✅ Relationship with Payment
    payments = db.relationship('Payment', back_populates='user', cascade='all, delete-orphan')



# Room Model
class Room(db.Model):
    __tablename__ = 'room'  # Ensure table name consistency
    
    room_id = db.Column(db.Integer, primary_key=True)  
    room_type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    availability = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text, nullable=True)
    room_image = db.Column(db.String(100), nullable=True)
    amenity = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Room {self.room_type}>'


class Payment(db.Model):
    __tablename__ = 'payments'

    payment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.booking_id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum('pending', 'completed'), default='pending')
    payment_date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    transaction_id = db.Column(db.String(100), nullable=True)

    # Specify the relationship with Booking
    booking = db.relationship('Booking', back_populates='payment', foreign_keys=[booking_id])

    user = db.relationship('User', back_populates='payments')


class Booking(db.Model):
    __tablename__ = 'booking'

    booking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.room_id', ondelete='CASCADE'), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')
    total_amount = db.Column(db.Numeric(10, 2), nullable=True)
    payment_status = db.Column(db.Enum('pending', 'completed', 'not_required'), default='pending')

    # Relationship to Payment (via booking_id)
    payment = db.relationship('Payment', back_populates='booking', uselist=False, foreign_keys="Payment.booking_id")

    user = db.relationship('User', backref=db.backref('bookings', lazy='joined'))
    room = db.relationship('Room', backref=db.backref('bookings', lazy='joined'))


# -----------------------
# Database Initialization
# -----------------------
# Admin creation script
# Admin creation script with consistent username and password logic
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
with app.app_context():
    db.create_all()

    # Check if admin user exists
    admin = User.query.filter_by(email='admin@hotel.com').first()

    if not admin:
        admin_password = generate_password_hash('admin1234', method='pbkdf2:sha256')  # 💡 Explicit method
        admin_user = User(
            username='admin',
            email='admin@hotel.com',
            password=admin_password,
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin user created. Username: admin, Password: admin1234")
    else:
        print("✅ Admin user already exists.")




def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="hotel_project"
    )



# Email Configuration
EMAIL_HOST = "smtp.gmail.com"  # Use your email provider
EMAIL_PORT = 587
EMAIL_ADDRESS = "livehomely@gmail.com"  # Change to your email
EMAIL_PASSWORD = "gjat iasn mmxv bjod"  # Use App Password (if using Gmail)

# Function to send OTP
def send_otp(email, otp):
    subject = "Password Reset OTP - LiveHomely"
    body = f"Your OTP for password reset is: {otp}. This OTP is valid for 10 minutes."
    
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False



# Forgot Password Route (Step 1: Enter Email)
@app.route('/forgotpassword', methods=['GET', 'POST'])
def forgotpassword():
    if request.method == 'POST':
        email = request.form.get('email')

        # Check if email exists in database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            otp = random.randint(100000, 999999)  # Generate OTP
            session['otp'] = otp  # Store OTP in session
            session['email'] = email  # Store email in session

            # Send OTP to user email
            if send_otp(email, otp):
                flash("OTP sent to your email. Check your inbox.", "success")
                return redirect(url_for('verify_otp'))
            else:
                flash("Error sending OTP. Try again later.", "danger")
        else:
            flash("Email not found. Please enter a registered email.", "danger")

    return render_template('forgotpassword.html')



# OTP Verification Route (Step 2: Enter OTP & New Password)
@app.route('/verifyotp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        new_password = request.form.get('password')

        if 'otp' not in session or 'email' not in session:
            session.pop('otp', None)
            session.pop('email', None)
            flash("Session expired. Try again.", "danger")
            return redirect(url_for('forgotpassword'))

        if int(entered_otp) == session['otp']:
            hashed_password = generate_password_hash(new_password)
            email = session['email']

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE user SET password = %s WHERE email = %s", (hashed_password, email))
            conn.commit()
            cursor.close()
            conn.close()

            # Clear session
            session.pop('otp', None)
            session.pop('email', None)

            flash("Password updated successfully! You can now log in.", "success")
            return redirect(url_for('login'))
        else:
            flash("Invalid OTP. Please try again.", "danger")

    return render_template('verifyotp.html')  # Fix infinite redirect loop







# -----------------------
# Routes
# -----------------------

@app.route('/')
def home():
    """ Home page with room listings """
    rooms = Room.query.all()  # Fetch all rooms from the database
    return render_template('home.html', rooms=rooms)  # ✅ Pass rooms to the template



@app.route('/index')
def index():
    if 'user_id' in session:
        return redirect(url_for('user_dashboard') if not session['is_admin'] else url_for('admin_dashboard'))
    return render_template('index.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login Route with Profile Completion Check"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Email or Password field is missing!', 'danger')
            return redirect(url_for('login'))

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['email'] = user.email
            session.permanent = True
            session['is_admin'] = False
            
            # ✅ Admin Check
            if hasattr(user, 'is_admin') and user.is_admin:
                session['is_admin'] = True
                flash('Welcome Admin!', 'success')
                return redirect(url_for('admin_dashboard'))

            # ✅ First-time login → Profile not complete
            if not user.profile_complete:
                flash('Please complete your profile first.', 'info')
                return redirect(url_for('edit_profile'))

            # ✅ Subsequent logins → Go to dashboard directly
            flash('Login successful!', 'success')
            return redirect(url_for('user_dashboard'))

        else:
            flash('Invalid email or password', 'danger')

    return render_template('index.html')






# ✅ Edit Profile Route (Image Upload Handling)
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    """ Edit profile route for first-time login """
    if 'user_id' not in session:
        flash('Please log in first!', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    if request.method == 'POST':
        # ✅ Update profile fields
        user.fname = request.form.get('first_name')
        user.lname = request.form.get('last_name')
        user.contact = request.form.get('contact')
        user.dob = datetime.strptime(request.form.get('dob'), '%Y-%m-%d')
        user.address = request.form.get('address')
        user.gender = request.form.get('gender')

        # ✅ Handle profile image upload
        if 'profile_image' in request.files:
            image = request.files['profile_image']
            if image and image.filename != '':
                filename = secure_filename(image.filename)
                
                # ✅ Add extension if missing
                if not os.path.splitext(filename)[1]:
                    filename += '.jpg'  # Add jpg extension by default

                image.save(os.path.join('static/images', filename))
                user.profile_image = filename

        # ✅ Mark profile as complete
        user.profile_complete = True
        db.session.commit()

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('edit_profile.html', user=user)




@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('admin_dashboard' if session['is_admin'] else 'user_dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        entered_otp = request.form['otp']
        password = request.form['password']

        # ✅ Step 1: Check if OTP matches
        if 'otp' not in session or int(session['otp']) != int(entered_otp):
            flash('Invalid OTP. Please try again.', 'danger')
            return redirect(url_for('register'))  # Stay on the same page

        # ✅ Step 2: Check if username or email already exists
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        if existing_user:
            flash('Username already exists', 'warning')
        elif existing_email:
            flash('Email already registered', 'warning')
        else:
            # ✅ Step 3: Save user in the database
            new_user = User(
                username=username,
                email=email,
                password=generate_password_hash(password)
            )
            db.session.add(new_user)
            db.session.commit()

            # ✅ Step 4: Clear session and redirect to Login Page
            session.pop('otp', None)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))  # ✅ Go directly to Login Page

    return render_template('register.html')  # Stay on registration page if anything fails



@app.route('/verify_registration_otp', methods=['GET', 'POST'])
def verify_registration_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']

        if 'otp' not in session:
            flash('Session expired. Please register again.', 'warning')
            return redirect(url_for('register'))

        if int(entered_otp) == session['otp']:  # ✅ OTP is correct
            # ✅ Save user data in the database
            new_user = User(
                username=session['username'],
                email=session['email'],
                password=session['password']
            )
            db.session.add(new_user)
            db.session.commit()

            # ✅ Clear session after successful registration
            session.pop('otp', None)
            session.pop('username', None)
            session.pop('email', None)
            session.pop('password', None)

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))  # ✅ Redirect to Login Page

        else:
            flash('Invalid OTP. Try again.', 'danger')

    return render_template('verify_registration_otp.html')


import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText


# Email Configuration
EMAIL_HOST = "smtp.gmail.com"  # Use your email provider
EMAIL_PORT = 587
EMAIL_ADDRESS = "livehomely@gmail.com"  # Change to your email
EMAIL_PASSWORD = "jnyu vyny txfi avac"  # Use App Password (if using Gmail)



# Explicitly load .env
dotenv_path = "E:\\HOTEL_RESERVATION\\.env"  # Adjust path if needed
load_dotenv(dotenv_path=dotenv_path)

def send_otp(email, otp):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("EMAIL_PASSWORD")

    if not sender_email or not sender_password:
        print("❌ Error: Environment variables for email credentials are not set!")
        return False

    subject = "Your OTP for Registration"
    body = f"Your OTP is: {otp}. Use this to complete your registration."
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()
        print("✅ OTP Sent Successfully!")
        return True
    except Exception as e:
        print("❌ Error sending email:", e)
        return False





@app.route('/send_otp', methods=['POST'])
def send_otp_request():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"message": "Email is required"}), 400

    otp = random.randint(100000, 999999)
    session["otp"] = otp
    session["email"] = email

    if send_otp(email, otp):
        return jsonify({"message": "OTP sent successfully"}), 200
    else:
        return jsonify({"message": "Failed to send OTP"}), 500





@app.route('/check_email', methods=['POST'])
def check_email():
    email = request.form['email']
    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return "Email already registered", 400
    return ""







# Verify user records
with app.app_context():
    users = User.query.all()
    for user in users:
        print(f"email: {user.email}, Password: {user.password}")

    # Optionally, reset the admin password
    admin = User.query.filter_by(email='admin').first()
    if admin:
        admin.password = generate_password_hash('admin1234')
        db.session.commit()
        print("Admin password reset to admin1234")




@app.route('/about')
def about():
    """Display the About Us page"""
    return render_template('about.html')




# Debug: Print all registered routes
print("Registered routes:")
for rule in app.url_map.iter_rules():
    print(rule.endpoint, rule.rule)






@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))




# -----------------------
# USER_DASHBOARD
# -----------------------
@app.route('/user_dashboard')
def user_dashboard():
    """ User Dashboard """
    if 'user_id' not in session:
        flash("Please log in!", "danger")
        return redirect(url_for('login'))

    # ✅ Fetch the logged-in user
    user = User.query.get(session['user_id'])

    # ✅ Print for debugging
    print("User Image Path:", user.profile_image)  # 🔥 Check image path in terminal

    # 💡 Check if user exists
    if not user:
        flash("User not found. Please log in again.", "warning")
        return redirect(url_for('login'))

    # ✅ Fetch bookings for the logged-in user
    bookings = Booking.query.filter_by(user_id=session['user_id']).all()

    # ✅ Pass both `user` and `bookings` to the template
    return render_template('user_dashboard.html', user=user, bookings=bookings)


# ✅ Route to delete a user
@app.route('/delete_user/<int:user_id>', methods=['GET'])
def delete_user(user_id):
    """Route to delete a user."""
    
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    try:
        user = User.query.get_or_404(user_id)

        # ✅ Delete the user
        db.session.delete(user)
        db.session.commit()

        flash('User deleted successfully!', 'success')
        return redirect(url_for('customer_management'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('customer_management'))









@app.route('/base')
def base():
    return render_template('base.html')





# -----------------------
# ADMIN_SITE
# -----------------------



# ✅ Admin dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    """ Admin Dashboard with Rooms and Bookings """
    if 'user_id' not in session or not session.get('is_admin'):
        flash("Please log in as admin!", "danger")
        return redirect(url_for('index'))

    try:
        # Fetch all room details
        rooms = Room.query.all()   # <-- Added query to fetch rooms

        # Fetch bookings with relationships
        bookings = (
            db.session.query(Booking)
            .join(User, Booking.user_id == User.id)
            .join(Room, Booking.room_id == Room.room_id)
            .add_columns(
                Booking.booking_id,
                User.username.label('username'),
                Room.room_type.label('room_type'),
                Booking.check_in,
                Booking.check_out,
                Booking.guests,
                Booking.status
            )
            .order_by(Booking.check_in.desc())
            .all()
        )

        # System stats
        total_rooms = len(rooms)
        active_bookings = len(bookings)
        pending_bookings = sum(1 for booking in bookings if booking.status == 'pending')
        available_rooms = sum(1 for room in rooms if room.availability)

        return render_template(
            'admin_dashboard.html',
            bookings=bookings,
            rooms=rooms,    # <-- Added rooms to the template
            total_rooms=total_rooms,
            active_bookings=active_bookings,
            pending_bookings=pending_bookings,
            available_rooms=available_rooms
        )

    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('base'))





@app.route('/admin_logout')
def admin_logout():
    """Admin Logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    flash('Logged out successfully', 'info')
    return redirect(url_for('home'))


from flask import make_response

@app.route('/room_management')
def room_management():
    """ Room Management Page """
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('login'))

    # ✅ Fetch the latest rooms from the database
    rooms = Room.query.order_by(Room.room_id.desc()).all()

    # ✅ Prevent caching
    response = make_response(render_template('room_management.html', rooms=rooms))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response



# ✅ Booking Management Route
@app.route('/booking_management')
def booking_management():
    """ Render Booking Management Page """
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))

    bookings = Booking.query.all()
    return render_template('booking_management.html', bookings=bookings)


# ✅ Customer Management Route
@app.route('/customer_management')
def customer_management():
    """ Render Customer Management Page """
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))

    customers = User.query.filter_by(is_admin=False).all()
    return render_template('customer_management.html', customers=customers)


# -----------------------
# BOOKING
# -----------------------

@app.route('/book/<int:room_id>', methods=['GET', 'POST'])
def booking(room_id):
    """Route to handle room booking with date validation."""

    if 'user_id' not in session:
        flash('Please log in to book a room.', 'danger')
        return redirect(url_for('login'))

    # ✅ Fetch the room
    room = Room.query.get_or_404(room_id)

    # ✅ Check if the room is available
    if not room.availability:
        flash('This room is already booked.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        try:
            # ✅ Get current date
            today = datetime.today().date()

            # ✅ Fetch form data
            check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%d').date()
            check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%d').date()
            guests = int(request.form['guests'])

            # 🚫 **Validation: Check-in date cannot be in the past**
            if check_in < today:
                flash('Check-in date cannot be in the past.', 'warning')
                return redirect(url_for('booking', room_id=room_id))

            # 🚫 **Validation: Check-out must be after check-in**
            if check_out <= check_in:
                flash('Check-out date must be after check-in date.', 'warning')
                return redirect(url_for('booking', room_id=room_id))

            # 🚫 **Validation: Max booking duration (7 days)**
            max_checkout = check_in + timedelta(days=7)
            if check_out > max_checkout:
                flash('You can only book a room for up to 7 days.', 'warning')
                return redirect(url_for('booking', room_id=room_id))

            # 🚫 **Validation: Same-day booking prevention**
            if check_in == today:
                flash('Same-day bookings are not allowed.', 'warning')
                return redirect(url_for('booking', room_id=room_id))

            # ✅ Check for overlapping bookings (ignoring cancelled bookings)
            conflicting_booking = Booking.query.filter(
                Booking.room_id == room_id,
                Booking.status != 'cancelled',  # Ignore cancelled bookings
                Booking.check_in < check_out,
                Booking.check_out > check_in
            ).first()

            if conflicting_booking:
                flash('This room is already booked for the selected dates.', 'danger')
                return redirect(url_for('booking', room_id=room_id))

            # ✅ Create new booking
            new_booking = Booking(
                user_id=session['user_id'],
                room_id=room_id,
                check_in=check_in,
                check_out=check_out,
                guests=guests,
                status='pending'  # Initially 'pending'
            )

            db.session.add(new_booking)
            db.session.commit()

            flash('Room booked successfully! Your booking is pending confirmation.', 'success')
            return redirect(url_for('user_dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('booking', room_id=room_id))

    return render_template('booking.html', room=room)





# ✅ Function to Automatically Free Up Rooms
def auto_free_rooms():
    """ Automatically make rooms available after checkout and mark bookings as completed """
    try:
        today = datetime.today().date()

        # ✅ Fetch all expired bookings that haven't been marked completed
        expired_bookings = Booking.query.filter(
            Booking.check_out <= today,
            Booking.status != 'completed'
        ).all()

        for booking in expired_bookings:
            # ✅ Free up the room
            room = Room.query.get(booking.room_id)

            if room:
                room.availability = True  # Make the room available again
                booking.status = 'completed'  # Mark the booking as completed

        # ✅ Commit changes in bulk
        db.session.commit()
        print("✅ Expired bookings marked as completed, and rooms are freed up!")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in freeing up rooms: {e}")

# ✅ Initialize Scheduler
scheduler = BackgroundScheduler()

# ✅ Add the auto-free job to run every 24 hours
scheduler.add_job(auto_free_rooms, 'interval', hours=24)
scheduler.start()



# Route to handle booking submission
@app.route('/submit_booking', methods=['POST'])
def submit_booking():
    """ Handle booking submission """
    try:
        # Fetch form data
        user_id = int(request.form.get('user_id'))
        room_id = int(request.form.get('room_id'))
        check_in = datetime.strptime(request.form.get('check_in'), '%Y-%m-%d').date()
        check_out = datetime.strptime(request.form.get('check_out'), '%Y-%m-%d').date()
        guests = int(request.form.get('guests'))

        # Check if the room is available
        room = Room.query.get(room_id)
        if not room or not room.availability:
            flash('Room is no longer available.', 'danger')
            return redirect(url_for('home'))

        # Create a new booking
        new_booking = Booking(
            user_id=user_id,
            room_id=room_id,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            status='pending'
        )

        # Add booking and update room availability
        db.session.add(new_booking)
        room.availability = False  # Set room as booked
        db.session.commit()

        flash('Booking successful!', 'success')
        return redirect(url_for('user_dashboard'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('home'))




from flask import flash, redirect, url_for
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Twilio Credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

def send_sms(to, message):
    """ Function to send SMS using Twilio """
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    sms = client.messages.create(
        body=message,
        from_=TWILIO_PHONE_NUMBER,
        to=to
    )
    
    return sms.sid  # Returns message SID

@app.route('/accept_booking/<int:booking_id>')
def accept_booking(booking_id):
    """ Accept booking and confirm it. """
    
    try:
        booking = Booking.query.get_or_404(booking_id)
        
        if booking.status != 'pending':
            flash('This booking is already processed.', 'warning')
            return redirect(url_for('booking_management'))

        # ✅ Confirm the booking
        booking.status = 'confirmed'

        # ✅ Mark the room as unavailable
        booking.room.availability = False

        db.session.commit()

        # ✅ Send SMS to User
        user_contact = booking.user.contact  
        message = f"Dear {booking.user.name}, your booking (ID: {booking.id}) is confirmed!"
        
        if user_contact:
            send_sms(user_contact, message)
            flash('Booking confirmed and SMS sent!', 'success')
        else:
            flash('Booking confirmed, but no phone number available to send SMS.', 'warning')

        return redirect(url_for('booking_management'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('booking_management'))



@app.route('/cancel_booking/<int:booking_id>')
def cancel_booking(booking_id):
    """Route to cancel a booking."""

    if 'user_id' not in session or not session.get('is_admin'):
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    try:
        booking = Booking.query.get_or_404(booking_id)

        # ✅ Mark room as available again
        room = Room.query.get(booking.room_id)
        if room:
            room.availability = True

        booking.status = 'cancelled'
        db.session.commit()

        flash('Booking cancelled successfully.', 'success')
        return redirect(url_for('admin_dashboard'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))


# ✅ Function to auto-update room availability
def update_room_availability():
    """Auto-available rooms after check-out."""
    today = datetime.today().date()
    expired_bookings = Booking.query.filter(Booking.check_out <= today, Booking.status != 'cancelled').all()

    for booking in expired_bookings:
        room = Room.query.get(booking.room_id)
        if room:
            room.availability = True
            booking.status = 'completed'  # Mark booking as completed
            db.session.commit()
    
    print("✅ Room availability updated!")

# ✅ Start the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(update_room_availability, 'interval', hours=24)  # Run every 24 hours
scheduler.start()


# -----------------------
# ROOMS
# -----------------------


# ✅ Keep this route (or choose the one you want to keep)
@app.route('/rooms')
def rooms():
    """Display all available rooms"""
    if 'user_id' not in session:
        flash('Please login to view available rooms.', 'warning')
        return redirect(url_for('login'))

    available_rooms = Room.query.filter_by(availability=True).all()
    if session['is_admin']:
        admin=True
    else:
        admin=False
    return render_template('room.html', rooms=available_rooms,admin=admin )





# Consistent upload folder configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')  # Use a single folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# File upload route
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)

    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)

    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('File uploaded successfully', 'success')
        return redirect(url_for('home'))



@app.route('/add_room', methods=['GET', 'POST'])
def add_room():
    """ Admin can add a new room """
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        try:
            # Extract form data
            room_type = request.form.get('room_type')
            price = float(request.form.get('price'))
            description = request.form.get('description')
            availability = True if request.form.get('availability') else False
            amenity = request.form.get('amenity', '')

            # ✅ Handle image upload
            room_image = ''
            image_file = request.files.get('room_image')

            if image_file and image_file.filename != '':
                if allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    
                    # Save the image
                    image_file.save(image_path)

                    # Store the relative path in the database
                    room_image = f'uploads/{filename}'
                else:
                    flash('Invalid file format. Only PNG, JPG, JPEG, and GIF allowed.', 'danger')
                    return redirect(url_for('add_room'))

            # ✅ Add the new room to the database
            new_room = Room(
                room_type=room_type,
                price=price,
                description=description,
                availability=availability,
                room_image=room_image,  # Save full image path
                amenity=amenity
            )

            db.session.add(new_room)
            db.session.commit()

            flash('Room added successfully!', 'success')
            return redirect(url_for('admin_dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('admin_dashboard'))

    # ✅ Render the form using GET request
    return render_template('add_room.html')





@app.route('/edit_room/<int:room_id>', methods=['GET', 'POST'])
def edit_room(room_id):
    """ Edit Room Details """
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('admin_dashboard'))

    room = Room.query.get_or_404(room_id)

    if request.method == 'POST':
        try:
            # Update room details
            room.room_type = request.form['room_type']
            room.price = float(request.form['price'])
            room.description = request.form['description']
            room.availability = 'availability' in request.form
            room.amenity = request.form['amenity']

            # Handle image upload
            image_file = request.files.get('room_image')

            if image_file and image_file.filename != '':
                if allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                    # Save new image
                    image_file.save(image_path)

                    # Remove old image
                    if room.room_image and os.path.exists(os.path.join('static', room.room_image)):
                        os.remove(os.path.join('static', room.room_image))

                    # Store new image path
                    room.room_image = f'uploads/{filename}'
                else:
                    flash('Invalid file format. Only PNG, JPG, JPEG, and GIF allowed.', 'danger')
                    return redirect(url_for('edit_room', room_id=room_id))

            db.session.commit()

            flash('Room updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('edit_room', room_id=room_id))

    return render_template('edit_room.html', room=room)



@app.route('/delete_room/<int:room_id>')
def delete_room(room_id):
    if 'user_id' not in session or not session['is_admin']:
        return redirect(url_for('index'))

    room = Room.query.get_or_404(room_id)
    db.session.delete(room)
    db.session.commit()
    flash('Room deleted successfully!', 'success')

    return redirect(url_for('admin_dashboard'))





# MAKE PAYMENT

@app.route('/make_payment/<int:booking_id>', methods=['GET', 'POST'])
def make_payment(booking_id):
    """Route for making payment."""
    try:
        booking = Booking.query.get_or_404(booking_id)

        # Check if payment already exists
        payment = Payment.query.filter_by(booking_id=booking_id).first()

        if not payment:
            # Create a new payment record if none exists
            payment = Payment(
                booking_id=booking.booking_id,
                user_id=booking.user_id,
                amount=booking.room.price,  # Fetch room price
                status='pending'
            )
            
            # ✅ Commit the payment first to generate payment_id
            db.session.add(payment)
            db.session.commit()

        # ✅ Now the payment_id is guaranteed to exist
        flash('Redirecting to payment gateway...', 'info')
        return redirect(url_for('payment_gateway', payment_id=payment.payment_id))

    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('user_dashboard'))


@app.route('/payment_gateway/<int:payment_id>', methods=['GET', 'POST'])
def payment_gateway(payment_id):
    """Simulated Payment Gateway"""

    # ✅ Fetch the payment
    payment = Payment.query.get_or_404(payment_id)

    # ✅ Fetch the associated booking
    booking = Booking.query.get_or_404(payment.booking_id)

    if request.method == 'POST':
        # ✅ Simulate payment completion
        payment.status = 'completed'
        payment.transaction_id = f'TXN-{int(time.time())}'  # Mock transaction ID
        db.session.commit()

        flash('Payment successful!', 'success')
        return redirect(url_for('user_dashboard'))

    # ✅ Pass both payment and booking objects to the template
    return render_template('payment_gateway.html', payment=payment, booking=booking)



@app.route('/payment/<int:booking_id>', methods=['GET', 'POST'])
def payment(booking_id):
    """ Payment Gateway Page """
    booking = Booking.query.get(booking_id)

    if not booking:
        flash("Booking not found!", "danger")
        return redirect(url_for('user_dashboard'))

    # Check if payment already exists
    payment = Payment.query.filter_by(booking_id=booking_id).first()

    if request.method == 'POST':
        if not payment:
            # ✅ Create new payment record
            payment = Payment(
                booking_id=booking_id,
                user_id=booking.user_id,
                amount=booking.total_amount,  # Correct payment amount
                status='completed',
                transaction_id=f'TXN-{int(time.time())}'
            )
            db.session.add(payment)
            db.session.commit()

            # ✅ Assign the payment_id to the booking after committing
            booking.payment_id = payment.payment_id
            db.session.commit()

            flash("Payment successful!", "success")
            return redirect(url_for('user_dashboard'))

        else:
            # ✅ Update existing payment
            payment.status = 'completed'
            payment.transaction_id = f'TXN-{int(time.time())}'
            db.session.commit()

            flash("Payment completed successfully!", "success")
            return redirect(url_for('user_dashboard'))

    return render_template('payment.html', booking=booking, payment=payment)

    # Render the payment page
    return render_template('payment.html', booking=booking, payment=payment)





# Ensure the invoices directory exists
if not os.path.exists("invoices"):
    os.makedirs("invoices")


@app.route('/generate_invoice/<int:booking_id>')
def generate_invoice(booking_id):
    """ Generate PDF Invoice for Booking """
    # Fetch booking details
    booking = Booking.query.get(booking_id)
    
    if not booking:
        flash("Booking not found", "danger")
        return redirect(url_for('user_dashboard'))

    # Fetch payment details
    payment = Payment.query.filter_by(booking_id=booking_id).first()

    if not payment:
        flash("Payment details not found", "danger")
        return redirect(url_for('user_dashboard'))

    # Fetch user details
    user = User.query.get(booking.user_id)

    # PDF Invoice Path
    invoice_filename = f"invoices/invoice_{booking_id}.pdf"
    
    # Create PDF
    doc = SimpleDocTemplate(invoice_filename, pagesize=LETTER)
    elements = []

    # Title
    elements.append(Paragraph(f"Hotel Reservation Invoice", style={'fontSize': 18, 'alignment': 1}))
    elements.append(Spacer(1, 12))

    # User Information
    user_info = f"""
    <b>Guest Name:</b> {user.username}<br/>
    <b>Email:</b> {user.email}<br/>
    <b>Booking ID:</b> {booking.booking_id}<br/>
    <b>Room:</b> Room {booking.room_id}<br/>
    <b>Check-in:</b> {booking.check_in}<br/>
    <b>Check-out:</b> {booking.check_out}<br/>
    <b>Guests:</b> {booking.guests}<br/>
    """
    elements.append(Paragraph(user_info))
    elements.append(Spacer(1, 12))

    # Payment Details Table
    table_data = [
        ['Description', 'Amount'],
        ['Room Charges', f"₹{booking.total_amount}"],
        ['Payment Method', payment.payment_method.capitalize()],
        ['Payment ID', payment.payment_id],
        ['Payment Date', payment.payment_date.strftime("%Y-%m-%d %H:%M:%S")],
    ]

    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    elements.append(Spacer(1, 24))

    # Footer
    footer = f"""
    <b>Thank you for your stay at our hotel!</b><br/>
    <b>Date:</b> {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    """
    elements.append(Paragraph(footer))

    # Build PDF
    doc.build(elements)

    # Send PDF file for download
    return send_file(invoice_filename, as_attachment=True)



if __name__ == '__main__':
    app.run(debug=True)
