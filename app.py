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
                    return jsonify({'success': True, 'redirect': url_for('submit_issue')})
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
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            role = data.get('role')

            if not all([email, password, role]):
                return jsonify({'success': False, 'message': 'All fields are required'}), 400

            with Db() as db:
                # Start transaction
                db.execute("START TRANSACTION")

                try:
                    # Check if email already exists
                    db.execute("SELECT email FROM admin WHERE email = %s", (email,))
                    if db.fetchone():
                        return jsonify({'success': False, 'message': 'Email already exists'}), 400

                    # Insert into department table first
                    query = """
                    INSERT INTO department (name)
                    VALUES (%s)
                    """
                    values = (role,)
                    db.execute(query, values)
                    dept_id = db.cursor.lastrowid

                    # Insert into admin table
                    query = """
                    INSERT INTO admin (name, email, password)
                    VALUES (%s, %s, %s)
                    """
                    values = (role, email, password)
                    db.execute(query, values)

                    # Insert into municipality/pwd table based on role
                    if role == "Municipality":
                        query = "INSERT INTO municipality (deptID) VALUES (%s)"
                        db.execute(query, (dept_id,))
                    elif role == "PWD":
                        query = "INSERT INTO pwd (deptID) VALUES (%s)"
                        db.execute(query, (dept_id,))

                    # Commit transaction
                    db.execute("COMMIT")

                    return jsonify({'success': True, 'message': 'User and department added successfully'})

                except Exception as e:
                    # Rollback on error
                    db.execute("ROLLBACK")
                    raise e

        except Exception as e:
            app.logger.error(f"Error adding user: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'message': 'An unexpected error occurred'}), 500

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

            # Determine department based on category
            with Db() as db:
                if category in ['Waste Management', 'Street Lights']:
                    db.execute("SELECT deptID FROM department WHERE name = 'Municipality'")
                else:
                    db.execute("SELECT deptID FROM department WHERE name = 'PWD'")
                
                dept_id = db.fetchone()[0]

                # Insert into complaint table
                query = """
                INSERT INTO complaint 
                    (description, photo, geoLocation, category, email, assignedDept)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                values = (description, filename, location, category, email, dept_id)
                db.execute(query, values)

                # Get the last inserted complaint ID
                complaint_id = db.cursor.lastrowid

                # Insert into imagerecognition table
                query = """
                INSERT INTO imagerecognition 
                    (model, detectedIssueType, complaintID)
                VALUES (%s, %s, %s)
                """
                values = ("yolo11", category, complaint_id)  # Use "yolo11" as the model name
                db.execute(query, values)

            # Return success message
            return jsonify({'success': True, 'message': 'Issue submitted successfully!'})

        except ValueError as ve:
            app.logger.error(f"Validation error: {str(ve)}", exc_info=True)
            return jsonify({'success': False, 'message': str(ve)}), 400
        except RuntimeError as re:
            app.logger.error(f"Runtime error: {str(re)}", exc_info=True)
            return jsonify({'success': False, 'message': str(re)}), 500
        except Exception as e:
            app.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
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
                ORDER BY id DESC
            """
            db.execute(query, (session.get('email'),))
            issues = db.fetchall()
            return jsonify(issues)
    except Exception as e:
        app.logger.error(f"Error fetching issues: {str(e)}")
        return jsonify([])

@app.route('/get-users')
def get_users():
    try:
        with Db() as db:
            query = """
                SELECT a.adminID, a.email, a.name, d.deptID
                FROM admin a
                JOIN department d ON a.name = d.name
            """
            db.execute(query)
            rows = db.fetchall()
            app.logger.info(f"Raw database rows: {rows}")  # Log raw database output
            
            users = [{
                'id': row[0],
                'email': row[1],
                'role': row[2],
                'deptID': row[3]
            } for row in rows]
            
            app.logger.info(f"Processed users: {users}")  # Log processed users
            return jsonify(users)
    except Exception as e:
        app.logger.error(f"Error fetching users: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/delete-user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        with Db() as db:
            # Get department ID first
            db.execute("""
                SELECT d.deptID 
                FROM department d
                JOIN admin a ON a.name = d.name
                WHERE a.adminID = %s
            """, (user_id,))
            dept_id = db.fetchone()[0]

            # Delete from admin table
            db.execute("DELETE FROM admin WHERE adminID = %s", (user_id,))
            
            # Delete from department table
            db.execute("DELETE FROM department WHERE deptID = %s", (dept_id,))
            
            # Delete from municipality/pwd tables if exists
            db.execute("DELETE FROM municipality WHERE deptID = %s", (dept_id,))
            db.execute("DELETE FROM pwd WHERE deptID = %s", (dept_id,))

        return jsonify({'success': True, 'message': 'User deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/update-user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        data = request.get_json()
        with Db() as db:
            # Update admin table
            db.execute("UPDATE admin SET email = %s, name = %s WHERE adminID = %s",
                      (data['email'], data['role'], user_id))
            
            # Update department table
            db.execute("""
                UPDATE department d
                JOIN admin a ON a.name = d.name
                SET d.name = %s
                WHERE a.adminID = %s
            """, (data['role'], user_id))

        return jsonify({'success': True, 'message': 'User updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.get_json()
        email = session.get('email')
        complaint_id = data.get('complaintID')
        rating = data.get('rating')
        comments = data.get('comments')

        with Db() as db:
            query = """
            INSERT INTO feedback 
                (email, complaintID, rating, comments)
            VALUES (%s, %s, %s, %s)
            """
            values = (email, complaint_id, rating, comments)
            db.execute(query, values)

        return jsonify({'success': True, 'message': 'Feedback submitted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True,)