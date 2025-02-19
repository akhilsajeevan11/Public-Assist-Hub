from flask import Flask, render_template  # <-- Add render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('report_issue.html') 


@app.route('/login')
def login():
    return render_template('login.html') 




if __name__ == '__main__':
    app.run(debug=True)