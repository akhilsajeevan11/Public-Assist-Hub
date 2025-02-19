from flask import Flask, render_template, request, redirect, url_for, session, jsonify  # <-- Add render_template, request, redirect, url_for, session, jsonify
import random
from flask_mail import Mail, Message
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables first

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER') 
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')  

mail = Mail(app)

@app.route('/')
def index():
    return render_template('login.html') 


@app.route('/home')
def home():
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





if __name__ == '__main__':
    app.run(debug=True)