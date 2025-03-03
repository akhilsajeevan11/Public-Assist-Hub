import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash  # <-- Add render_template, request, redirect, url_for, session, jsonify, flash
import random
from flask_mail import Mail, Message
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from datetime import datetime
import mysql.connector
from db_connection import Db 
import torch
from PIL import Image
from ultralytics import YOLO

# Initialize app before other imports
app = Flask(__name__)
# app.config.from_object(Config)


load_dotenv()  # Load environment variables first

app.secret_key = os.environ.get('SECRET_KEY')

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER') 
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')  

mail = Mail(app)

# Add these configurations before the directory creation
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif'}
app.config['UPLOAD_FOLDER'] = 'uploads'

# Then create the directory if it doesn't exist
if 'UPLOAD_FOLDER' in app.config:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
else:
    app.logger.warning("UPLOAD_FOLDER not configured, file uploads will fail")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    return render_template('login.html') 





@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            data = request.get_json()
            print("Data is..",data)
            if not data:
                return jsonify({'error': 'No data received'}), 400

            # Check if it's an OTP verification attempt
            if 'otp' in data:
                if 'otp' not in session:
                    return jsonify({'error': 'OTP session expired'}), 400
                
                if data['otp'] == session['otp']:
                    # Store in database before clearing session
                    with Db() as db:
                        query = """
                            INSERT INTO users (email, otp)
                            VALUES (%s, %s)
                            ON DUPLICATE KEY UPDATE otp = %s
                        """
                        values = (session['email'], session['otp'], session['otp'])
                        db.execute(query, values)
                    
                    session.pop('otp', None)
                    return jsonify({'success': True, 'redirect': url_for('home')})
                return jsonify({'error': 'Invalid OTP'}), 400

            # Handle email submission
            email = data.get('email')
            print("Email is...",email)
            if not email:
                return jsonify({'error': 'Email is required'}), 400

            otp = random.randint(100000, 999999)
            print("OTP is ...",otp)
            session['otp'] = str(otp)
            session['email'] = email

            try:
                msg = Message('Your Login OTP',
                            sender=app.config['MAIL_USERNAME'],
                            recipients=[email])
                msg.body = f'Your OTP is: {otp}'
                mail.send(msg)
                return jsonify({'message': 'OTP sent successfully'})
            except Exception as e:
                return jsonify({'error': f'Error sending email: {str(e)}'}), 500

        except Exception as e:
            return jsonify({'error': f'Server error: {str(e)}'}), 500

    return render_template('login.html')




@app.route('/municipality')
def municipality():
    return render_template('municipality.html') 



@app.route('/pwd')
def pwd():
    return render_template('pwd.html') 



@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        try:
            # Get form data
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            role = data.get('role')  # Municipality or PWD

            # Validate required fields
            if not all([email, password, role]):
                return jsonify({'success': False, 'message': 'All fields are required'}), 400

            # Insert into admin table
            with Db() as db:
                # Insert into admin table
                query = """
                INSERT INTO admin (name, email, password)
                VALUES (%s, %s, %s)
                """
                values = (role, email, password)
                db.execute(query, values)

                # Insert into department table
                query = """
                INSERT INTO department (name)
                VALUES (%s)
                """
                values = (role,)
                db.execute(query, values)

            return jsonify({'success': True, 'message': 'User and department added successfully'})

        except Exception as e:
            app.logger.error(f"Error adding user: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'message': 'An unexpected error occurred'}), 500

    # GET request handling
    return render_template('admin.html')



# Update the model loading code to:
model = YOLO(os.environ.get('YOLO_MODEL_PATH')) 

@app.route('/submit_issue', methods=['GET', 'POST'])
def submit_issue():
    if request.method == 'POST':
        try:
            # Validate required fields
            if not all(key in request.form for key in ['title', 'description', 'location']):
                raise ValueError("Missing required fields")
            
            title = request.form['title']
            description = request.form['description']
            location = request.form['location']
            image = request.files.get('image')
            email = session.get('email')

            # Process image and get prediction
            category = "General"  # Default category
            filename = None
            if image and image.filename != '':
                if not allowed_file(image.filename):
                    raise ValueError("Invalid file type")
                
                filename = secure_filename(f"{datetime.now().timestamp()}_{image.filename}")
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                image.save(upload_path)
                
                # YOLO prediction
                img = Image.open(image.stream)
                results = model.predict(img)
                if results and len(results[0]) > 0:
                    class_id = int(results[0].boxes.cls[0])
                    category = model.names[class_id]

            # Database insertion
            with Db() as db:
                query = """
                INSERT INTO complaint 
                    (description, photo, geoLocation, category, email)
                VALUES (%s, %s, %s, %s, %s)
                """
                values = (description, filename, location, category, email)
                db.execute(query, values)

            return redirect(url_for('submit_issue'))  # Redirect back to the submit issue page

        except ValueError as ve:
            return jsonify({'success': False, 'message': str(ve)}), 400
        except RuntimeError as re:
            return jsonify({'success': False, 'message': str(re)}), 500
        except Exception as e:
            return jsonify({'success': False, 'message': 'An unexpected error occurred.'}), 500
    
    # GET request handling
    return render_template('report_issue.html')


@app.route('/get_issues')
def get_issues():
    try:
        with Db() as db:
            query = """
                SELECT * FROM complaint
                WHERE email = %s
                ORDER BY created_at DESC
            """
            db.execute(query, (session.get('email'),))
            issues = db.fetchall()
            return jsonify(issues)
    except Exception as e:
        app.logger.error(f"Error fetching issues: {str(e)}")
        return jsonify([])


if __name__ == '__main__':
    app.run(debug=True,)