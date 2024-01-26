from flask import Flask, request, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os, random
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import secrets
from datetime import timedelta


app = Flask(__name__)
CORS(app, supports_credentials=True, methods=["GET", "HEAD", "POST", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Ido123@localhost/library'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking
app.config['UPLOAD_FOLDER'] = 'uploads'  # Folder to store uploaded files
app.config['SECRET_KEY'] = secrets.token_hex(16)  # Secret key for session management
app.config['JWT_SECRET_KEY'] = secrets.token_hex(16)  # Secret key for JWT

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Define models
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(255))
    name = db.Column(db.String(255))
    author = db.Column(db.String(255))
    year_published = db.Column(db.Integer)
    book_type = db.Column(db.Integer)
    

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    city = db.Column(db.String(50))
    age = db.Column(db.Integer)
    password = db.Column(db.String(255))

class Loan(db.Model):
    cust_id = db.Column(db.Integer, db.ForeignKey('customer.id'), primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), primary_key=True)
    loan_date = db.Column(db.DateTime)
    return_date = db.Column(db.DateTime)

    #method to calculate return date based on book type
    def calculate_return_date(self, book_type):
        if book_type == 1:
            return self.loan_date + timedelta(days=10)
        elif book_type == 2:
            return self.loan_date + timedelta(days=5)
        elif book_type == 3:
            return self.loan_date + timedelta(days=2)
        else:
            return None

# Checks if a folder "UPLOAD_FOLDER" exists and if not produces one
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    # Check if the file extension is allowed
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif'}

# Function to register a new customer
def register_customer(name, city, age, password):
    existing_customer = Customer.query.filter_by(name=name).first()
    if existing_customer:
        return jsonify(error="User with that name already exists"), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_customer = Customer(name=name, city=city, age=age, password=hashed_password)
    db.session.add(new_customer)
    db.session.commit()

    return jsonify(message="Registration successful"), 201

def authenticate_customer(name, password):
    customer = Customer.query.filter_by(name=name).first()
    if not customer or not bcrypt.check_password_hash(customer.password, password):
        return jsonify(error="Invalid credentials"), 401

    session['logged_in_customer'] = customer.id  # Store customer ID in the session

    # Check if the 'logged_in_customer' key is present in the session
    if 'logged_in_customer' in session:
        return jsonify(message="Login successful"), 200
    else:
        return jsonify(error="Failed to store session data"), 500

# Function to check if a customer is logged in
def is_logged_in():
    return 'logged_in_customer' in session

@app.route('/register', methods=['POST'])
def register_route():
    data = request.get_json()
    name = data.get('name')
    city = data.get('city')
    age = data.get('age')
    password = data.get('password')

    if not name or not city or not age or not password:
        return jsonify(error="Incomplete data provided"), 400

    return register_customer(name, city, age, password)

# login route
@app.route('/login', methods=['POST'])
def login_route():
    data = request.get_json()
    name = data.get('name')
    password = data.get('password')

    if not name or not password:
        return jsonify(error="Incomplete data provided"), 400

    customer = Customer.query.filter_by(name=name).first()

    if not customer or not bcrypt.check_password_hash(customer.password, password):
        return jsonify(error="Invalid credentials"), 401

    access_token = create_access_token(identity=customer.id)
    #welcome message
    welcome_message = f"Welcome, {customer.name}!"
    return jsonify(access_token=access_token, welcome_message=welcome_message), 200


# route to serve static files (images)
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# add_book route
@app.route('/add_book', methods=['POST'])
@jwt_required()
def add_book():
    current_user = get_jwt_identity()

    if not current_user:
        return jsonify(error="Unauthorized, please log in"), 401

    # Process file upload and book data
    file = request.files.get('file')  # Use get() to handle the case when 'file' is not present
    if file and (file.filename == '' or not allowed_file(file.filename)):
        return jsonify(error="Invalid file"), 400

    # Generate a unique filename based on book details
    name = request.form.get('name')
    author = request.form.get('author')
    year_published = request.form.get('year_published')
    book_type = request.form.get('book_type')

    # Ensure book type is 1, 2, or 3
    if book_type not in {'1', '2', '3'}:
        return jsonify(error="Invalid book type"), 400

    filename = request.form.get('image', 'open_book_def.jpg')  # Use the default image filename

    data = request.form.to_dict()
    data['image'] = filename  # Save the filename in the database

    # Create a new book
    new_book = Book(**data)
    db.session.add(new_book)
    db.session.commit()

    return_date = datetime.now() + timedelta(days=int(book_type))  # Calculate return date based on book type

    return jsonify(message="Book added successfully", return_date=return_date.strftime('%Y-%m-%d')), 201


# Function to get all books
@app.route('/books', methods=['GET'])
def get_all_books():
    books = Book.query.all()
    book_list = [{'id': book.id, 'name': book.name, 'author': book.author, 'year_published': book.year_published, 'book_type': book.book_type, 'image': book.image} for book in books]
    return jsonify(books=book_list)

# Function to get all customers
@app.route('/customers', methods=['GET'])
def get_all_customers():
    customers = Customer.query.all()
    customer_list = [{'name': customer.name, 'city': customer.city, 'age': customer.age} for customer in customers]
    return jsonify(customers=customer_list)

@app.route('/loans', methods=['GET'])
def get_all_loans():
    loans = Loan.query.all()
    loan_list = []

    for loan in loans:
        customer = Customer.query.get(loan.cust_id)
        book = Book.query.get(loan.book_id)

        loan_data = {
            'customer_name': customer.name,
            'book_name': book.name,
            'loan_date': loan.loan_date,
            'return_date': loan.return_date
        }
        loan_list.append(loan_data)

    return jsonify(loans=loan_list)

# find a book by name
@app.route('/find_book', methods=['GET'])
def find_book():
    book_name = request.args.get('name')

    if not book_name:
        return jsonify(error="Book name not provided"), 400

    # Search for the book by name
    book = Book.query.filter_by(name=book_name).first()

    if not book:
        return jsonify(error="Book not found"), 404

    book_data = {
        'id': book.id,
        'name': book.name,
        'author': book.author,
        'year_published': book.year_published,
        'book_type': book.book_type,
        'image': book.image
    }

    return jsonify(book=book_data)

#find a customer by name
@app.route('/find_customer', methods=['GET'])
def find_customer():
    customer_name = request.args.get('name')

    if not customer_name:
        return jsonify(error="Customer name not provided"), 400

    # Search for the customer by name
    customer = Customer.query.filter_by(name=customer_name).first()

    if not customer:
        return jsonify(error="Customer not found"), 404

    customer_data = {
        'id': customer.id,
        'name': customer.name,
        'city': customer.city,
        'age': customer.age
    }

    return jsonify(customer=customer_data)

@app.route('/get_book/<int:book_id>', methods=['GET'])
@jwt_required()
def get_book(book_id):
    current_user = get_jwt_identity()

    book = Book.query.filter_by(id=book_id).first()
    if not book:
        return jsonify(error="Book not found"), 404

    # Check if the book is loaned by the current user
    is_loaned = Loan.query.filter_by(cust_id=current_user, book_id=book.id).first()

    book_data = {
        'id': book.id,
        'image': book.image,
        'name': book.name,
        'author': book.author,
        'year_published': book.year_published,
        'book_type': book.book_type,
        'is_loaned': bool(is_loaned)  # Add a flag indicating if the book is loaned by the user
    }

    return jsonify(book=book_data)

@app.route('/add_loan', methods=['POST'])
@jwt_required()
def add_loan():
    current_user = get_jwt_identity()

    data = request.get_json()
    book_id = data.get('bookId')

    # Check if the book exists
    book = Book.query.get(book_id)
    if not book:
        return jsonify(error="Book not found"), 404

    # Check if the book is already loaned
    existing_loan = Loan.query.filter_by(book_id=book_id).first()
    if existing_loan:
        return jsonify(error="Book already loaned by another customer"), 400

    # Calculate return date based on book type
    return_date = datetime.now() + timedelta(days=int(book.book_type))

    new_loan = Loan(cust_id=current_user, book_id=book_id, loan_date=datetime.now(), return_date=return_date)
    db.session.add(new_loan)
    db.session.commit()

    return jsonify(message="Book loaned successfully"), 201


@app.route('/update_book', methods=['POST'])
@jwt_required()
def update_book():
    current_user = get_jwt_identity()

    data = request.get_json()
    book_id = data.get('bookId')
    updated_name = data.get('updatedName')
    updated_author = data.get('updatedAuthor')
    updated_year_published = data.get('updatedYearPublished')
    updated_book_type = data.get('updatedBookType')

    # Check if the book exists
    book = Book.query.get(book_id)
    if not book:
        return jsonify(error="Book not found"), 404

    # Update the book details
    book.name = updated_name
    book.author = updated_author
    book.year_published = updated_year_published
    book.book_type = updated_book_type

    db.session.commit()

    return jsonify(message="Book updated successfully"), 200

@app.route('/my_loans', methods=['GET'])
@jwt_required()
def get_my_loans():
    current_user = get_jwt_identity()

    # Retrieve loans for the current user
    my_loans = Loan.query.filter_by(cust_id=current_user).all()

    my_loans_list = []

    for loan in my_loans:
        book = Book.query.get(loan.book_id)

        loan_data = {
            'book_name': book.name,
            'loan_date': loan.loan_date.strftime('%Y-%m-%d'),
            'return_date': loan.return_date.strftime('%Y-%m-%d')
        }
        my_loans_list.append(loan_data)

    return jsonify(my_loans=my_loans_list)

@app.route('/return_loan', methods=['POST'])
@jwt_required()
def return_loan():
    current_user = get_jwt_identity()
    data = request.get_json()
    book_name = data.get('bookName')

    # Find the book by name
    book = Book.query.filter_by(name=book_name).first()

    if not book:
        return jsonify(error="Book not found"), 404

    # Find the loan for the current user and the specified book
    loan = Loan.query.filter_by(cust_id=current_user, book_id=book.id).first()

    if not loan:
        return jsonify(error="Loan not found"), 404

    # Delete the loan
    db.session.delete(loan)
    db.session.commit()

    return jsonify(message="Loan returned successfully"), 200


# Add three customers test unit
@app.route('/add_three_customers', methods=['POST'])
def add_three_customers():
    try:
        for i in range(3):
            # Generate a random name
            random_name = f'User{i + 1}'

            # Randomly pick one of the options from the list for city
            cities = ['New York', 'London', 'Tokyo', 'Paris', 'Berlin']
            random_city = random.choice(cities)

            # Generate random age between 18 and 65
            random_age = random.randint(18, 65)

            # Assume password is constant for simplicity
            password = '123'

            # Call your existing function to add the new customer
            register_customer(random_name, random_city, random_age, password)

        return jsonify({'message': 'Three customers added successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/add_three_books', methods=['POST'])
def add_three_books():
    try:
        for i in range(3):
            # Generate book data
            random_name = f'Book{i + 1}'
            random_author = f'Author{i + 1}'
            random_year_published = str(random.randint(1800, 2022))  # Change this range based on your requirements
            random_book_type = str(random.choice([1, 2, 3]))

            # Ensure book type is 1, 2, or 3
            if random_book_type not in {'1', '2', '3'}:
                return jsonify(error="Invalid book type"), 400

            filename = 'open_book_def.jpg'  # Use the default image filename

            data = {
                'name': random_name,
                'author': random_author,
                'year_published': random_year_published,
                'book_type': random_book_type,
                'image': filename
            }

            # Create a new book
            new_book = Book(**data)
            db.session.add(new_book)
            db.session.commit()

        return jsonify({'message': 'Three books added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

    
# Add three loans route
@app.route('/add_three_loans', methods=['POST'])
def add_three_loans():
    try:
        # Get the first 3 available customers and books
        available_customers = Customer.query.limit(3).all()
        available_books = Book.query.limit(3).all()

        if not available_customers or not available_books:
            return jsonify({'error': 'Not enough customers or books available'}), 400

        for customer in available_customers:
            for book in available_books:
                # Check if the book is already loaned
                existing_loan = Loan.query.filter_by(book_id=book.id).first()
                if existing_loan:
                    continue

                # Calculate return date based on book type
                return_date = datetime.now() + timedelta(days=int(book.book_type))

                new_loan = Loan(cust_id=customer.id, book_id=book.id, loan_date=datetime.now(), return_date=return_date)
                db.session.add(new_loan)
                db.session.commit()

        return jsonify({'message': 'Three loans added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/late_loans', methods=['GET'])
def get_late_loans():
    current_time = datetime.now()
    late_loans = Loan.query.filter(Loan.return_date < current_time).all()

    if not late_loans:
        return jsonify(message="No late loans at the moment"), 200

    late_loans_list = []

    for loan in late_loans:
        customer = Customer.query.get(loan.cust_id)
        book = Book.query.get(loan.book_id)
        days_late = (current_time - loan.return_date).days

        late_loan_data = {
            'customer_name': customer.name,
            'book_name': book.name,
            'days_late': days_late
        }
        late_loans_list.append(late_loan_data)

    return jsonify(late_loans=late_loans_list), 200
    

@app.route('/')
def index():
    if is_logged_in():
        # Get the current customer's name
        current_user = get_jwt_identity()
        customer = Customer.query.get(current_user)
        customer_name = customer.name if customer else "Customer"

        return jsonify(message=f"Welcome, {customer_name}!")

    return jsonify(message="Library Management System")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
