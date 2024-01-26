# Library Management System

This Flask application serves as a versatile Library Management System, providing a robust platform for organizing and managing your library's resources. Below are additional details about the system and its usage.

## Features

- **User Authentication**: Securely manage user access with a registration and login system. Passwords are hashed for enhanced security.

- **Book Management**: Efficiently add, retrieve, and update book details, including name, author, year published, and book type.

- **Customer Management**: Streamline customer registration with essential details such as name, city, and age.

- **Loan Management**: Effectively handle book loans, calculating return dates based on book types, and monitoring late loans.

- **Image Upload**: Enhance the user experience by supporting image uploads for book covers.

## System Usage

### Registration and Login

To access the system, users can register with their details, including name, city, age, and a secure password. Subsequently, the login functionality allows users to authenticate themselves and access personalized features.

### Adding Books

Librarians can easily add new books to the system by providing details such as the book's name, author, publication year, and type. Additionally, the system supports image uploads for book covers, making the library visually appealing.

### Managing Customers

Efficiently manage customer information by registering new customers and maintaining accurate records of their names, cities, and ages.

### Handling Loans

The system facilitates the loaning of books to customers. It calculates return dates based on book types, ensuring a streamlined and organized lending process. Librarians can monitor loans and identify any overdue items.

### Testing and Sample Data

For testing purposes, the system includes routes to add three customers, three books, and three loans as a test unit. This feature is handy for evaluating the system's functionality in a controlled environment.

## Setup

1. **Clone the repository:**

    ```bash
    git clone https://github.com/Ido2025/librery_py.git
    ```

2. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Set up the MySQL database:**

    Modify the `SQLALCHEMY_DATABASE_URI` in `app.py` with your database connection details.

4. **Run the application:**

    ```bash
    python app.py
    ```

5. **Access the application:**

    Open your web browser and go to [http://localhost:5000](http://localhost:5000).

## Customization

Feel free to customize the application to suit your library's unique needs. Explore and extend its functionality to create a tailored solution for your library management.

## Note

- Ensure that the necessary dependencies are installed before running the application.

- Customize the database connection details in `app.py` according to your MySQL setup.

- JWT authentication is required for certain endpoints. Include the generated access token in the request headers.

- This application uses MySQL as the database. Modify the database URI in `app.py` to use a different database.

We hope this Library Management System enhances the efficiency and organization of your library's operations. If you have any questions or feedback, please feel free to reach out.
