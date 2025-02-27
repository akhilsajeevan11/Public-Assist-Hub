import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash  # <-- Add render_template, request, redirect, url_for, session, jsonify, flash
import random
from flask_mail import Mail, Message
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from datetime import datetime
import mysql.connector

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



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    return render_template('login.html') 


@app.route('/submit_issue', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        try:
            # Validate required fields
            if not all(key in request.form for key in ['title', 'description', 'location']):
                raise ValueError("Missing required fields")
            
            title = request.form['title']
            print("title iss",title)
            description = request.form['description']
            location = request.form['location']
            image = request.files.get('image')  # Use get() to avoid KeyError
            print("Image is ..",image)

            filename = None
            if image and image.filename != '':  # Check for empty filename
                if not allowed_file(image.filename):
                    raise ValueError("Invalid file type")
                
                filename = secure_filename(f"{datetime.now().timestamp()}_{image.filename}")
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                image.save(upload_path)

            # Modified database insertion
            with Db() as db:
                query = """
                INSERT INTO issues 
                    (title, description, image, location, status, created_at)
                VALUES (%s, %s, %s, %s, 'Reported', NOW())
                """
                values = (title, description, filename, location)
                
                try:
                    issue_id = db.insert(query, values)
                except mysql.connector.Error as err:
                    app.logger.error(f"Database error: {err}")
                    raise RuntimeError("Failed to save issue to database")

            flash('Issue reported successfully!', 'success')
            return redirect(url_for('home'))

        except ValueError as ve:
            app.logger.warning(f"Validation error: {str(ve)}")
            flash(str(ve), 'warning')
        except RuntimeError as re:
            app.logger.error(f"Database operation failed: {str(re)}")
            flash('Database error. Please try again.', 'danger')
        except Exception as e:
            app.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            flash('An unexpected error occurred. Please try again.', 'danger')
            
        return redirect(url_for('submit_issue'))
    
    # GET request handling
    return render_template('report_issue.html')




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            data = request.get_json()  # Get JSON data instead of form data
            print("Data is..",data)
            if not data:
                return jsonify({'error': 'No data received'}), 400

            # Check if it's an OTP verification attempt
            if 'otp' in data:
                if 'otp' not in session:
                    return jsonify({'error': 'OTP session expired'}), 400
                
                if data['otp'] == session['otp']:
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



@app.route('/admin')
def admin():
    return render_template('admin.html') 



if __name__ == '__main__':
    app.run(debug=True,)