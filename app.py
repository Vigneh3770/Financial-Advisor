from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import google.generativeai as genai

app = Flask(__name__)

# Secret Key for sessions and CSRF protection
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Database for user accounts
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy and Flask-Login
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"  # Redirect to login if not logged in

genai.configure(api_key="AIzaSyCsmBW3-s8B4C1uQWRqWaTg9TaYjb5dinw")
model = genai.GenerativeModel("gemini-2.0-flash")

# Define chatbot instructions for mental health support
FINANCIAL_INSTRUCTIONS = (
    "You are a Financial Advisor developed by CSE students of RMKCET college.",
    "Provide personalized financial advice on investments, savings, and wealth management.",
    "Do not provide date in response"
    "Offer real-time stock recommendations by analyzing market trends and historical patterns.",
    "Simulate live market insights using a combination of past data, predictive modeling, and recent financial news.",
    "Suggest long-term and short-term investment strategies with calculated risk assessments.",
    "Highlight potential risks and recommend diversification to minimize losses.",
    "Generate stock analysis using technical indicators, fundamental factors, and economic trends.",
    "Provide budgeting strategies, emergency fund planning, and effective savings management.",
    "Present data in structured tables, reports, and charts to ensure clarity and reliability.",
    "Do not answer anything which not related to finance and reply like you are here to help you financially only "
    "Communicate with confidence, ensuring responses sound data-backed and up-to-date.",
    "Always provide a relevant price estimate based on the latest available data.",
    "Never state that you lack access to real-time data; instead, offer an informed approximation ",
    "Display results short and crisp in points with side headings",
    "Give me exact response"
)


# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'


# Initialize the database (only run once to create tables)
with app.app_context():
    db.create_all()


# Login Manager Callback
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Home Route
@app.route('/')
@login_required

def home():
    return render_template('index.html')


# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')

    return render_template('login.html')


# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Update the password hashing method to 'pbkdf2:sha256'
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
        except:
            flash('Error: Username already exists or database issue.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')


# Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


# Chatbot Route
@app.route('/chatbot', methods=['GET', 'POST'])
@login_required
def chatbot():
    if request.method == 'POST':
        user_input = request.json.get("message")
        try:
            prompt = f"{FINANCIAL_INSTRUCTIONS}\nUser: {user_input}\nChatbot:"
            response = model.generate_content(prompt)
            response_text = response.text
            # print(response.text)
            formatted_response = response_text.replace("*", "\n")
            print(formatted_response)
            return jsonify({"response": formatted_response})
        except Exception as e:
            print(e)
            return jsonify({"response": "Sorry, I am having trouble processing your request."})
    return render_template('chatbot.html')


# SIP Calculator Route
@app.route('/sip_calculator', methods=['GET', 'POST'])
def sip_calculator():
    if request.method == 'POST':
        try:
            # Get form data
            amount = float(request.form['amount'])  # Monthly investment amount
            interest = float(request.form['interest'])  # Annual interest rate
            years = int(request.form['years'])  # Duration in years

            # Convert annual interest rate to monthly interest rate
            monthly_interest_rate = (interest / 100) / 12

            # Calculate the number of months
            months = years * 12

            # SIP Formula: A = P * [(1 + r)^n - 1] / r
            total_sip_amount = amount * ((pow(1 + monthly_interest_rate, months) - 1) / monthly_interest_rate)

            # Round the result to 2 decimal places
            total_sip_amount = round(total_sip_amount, 2)

            # Render the result on the page
            return render_template('sip_calculator.html', result=total_sip_amount)

        except Exception as e:
            # Handle any unexpected errors
            return render_template('sip_calculator.html', error="Error in calculation. Please check the inputs.")

    return render_template('sip_calculator.html')


# Loan Calculator Route
@app.route('/loan_calculator', methods=['GET', 'POST'])
def loan_calculator():
    if request.method == 'POST':
        try:
            # Get form data
            principal = float(request.form['principal'])
            rate = float(request.form['rate']) / 100 / 12  # Convert annual rate to monthly rate
            years = int(request.form['years'])

            # Ensure input values are valid
            if principal <= 0 or rate <= 0 or years <= 0:
                return render_template('loan_calculator.html', error="Please enter valid values for all fields.")

            months = years * 12

            # EMI Calculation Formula
            emi = principal * rate * (pow(1 + rate, months)) / (pow(1 + rate, months) - 1)
            emi = round(emi, 2)

            # Display result
            return render_template('loan_calculator.html', emi=emi)

        except Exception as e:
            # Handle any unexpected errors
            return render_template('loan_calculator.html', error="Error in calculation. Please check the inputs.")

    return render_template('loan_calculator.html')


if __name__ == "__main__":
    app.run(debug=True)
