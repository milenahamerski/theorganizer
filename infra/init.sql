CREATE DATABASE IF NOT EXISTS theorganizer;

USE theorganizer;

CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    year INT,
    image_url VARCHAR(500)
);
