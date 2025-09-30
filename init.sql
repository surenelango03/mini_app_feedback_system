-- Reset database
DROP DATABASE IF EXISTS feedback_system;
CREATE DATABASE feedback_system;
USE feedback_system;

-- Tables
CREATE TABLE Users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,       -- Added password column
    role VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Vendors (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255) NOT NULL
);

CREATE TABLE Products (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    vendor_id BIGINT NOT NULL,
    FOREIGN KEY (vendor_id) REFERENCES Vendors(id) ON DELETE CASCADE
);

CREATE TABLE Feedback (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    comment VARCHAR(255),
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    product_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES Products(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
);

CREATE TABLE Review_Replies (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    reply_text VARCHAR(255),
    replied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    feedback_id BIGINT NOT NULL,
    vendor_id BIGINT NOT NULL,
    FOREIGN KEY (feedback_id) REFERENCES Feedback(id) ON DELETE CASCADE,
    FOREIGN KEY (vendor_id) REFERENCES Vendors(id) ON DELETE CASCADE
);

-- Sample Users with passwords (plain text)
INSERT INTO Users (name, email, password, role) VALUES
('Alice', 'alice@example.com', 'alice123', 'customer'),
('Bob', 'bob@example.com', 'bob123', 'customer'),
('Charlie', 'charlie@example.com', 'charlie123', 'customer'),
('ram', 'ram.admin@example.com', 'ram123', 'admin'),
('mahesh', 'mahesh.admin@example.com', 'mahesh123', 'admin'),
('kumar', 'kumar.admin@example.com', 'kumar123', 'admin');

-- Sample Vendors
INSERT INTO Vendors (name, contact_email) VALUES
('Gadget Store', 'gadgetstore@example.com'),
('Book World', 'bookworld@example.com');

-- Sample Products
INSERT INTO Products (name, description, vendor_id, created_at) VALUES
('Smartphone X', 'Latest model with OLED display', 1, NOW()),
('Wireless Headphones', 'Noise-cancelling over-ear headphones', 2, NOW()),
('Gaming Laptop', 'High performance laptop for gaming', 1, NOW()),
('Electric Kettle', 'Fast-boil 1.5L kettle', 2, NOW()),
('Bluetooth Speaker', 'Portable speaker with deep bass', 2, NOW());

-- Sample Feedback
INSERT INTO Feedback (comment, rating, product_id, user_id) VALUES
('Great phone, very smooth!', 5, 1, 1),
('Battery life could be better.', 3, 1, 2),
('Loved the sound quality!', 4, 2, 3),
('Amazing book, could not put it down.', 5, 3, 1);

-- Sample Review Replies
INSERT INTO Review_Replies (reply_text, feedback_id, vendor_id) VALUES
('Thank you for your feedback, Alice!', 1, 1),
('We will work on improving battery life.', 2, 1),
('Glad you enjoyed it!', 4, 2);
