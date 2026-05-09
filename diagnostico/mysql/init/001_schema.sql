CREATE DATABASE IF NOT EXISTS diagnostico CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE diagnostico;

CREATE TABLE sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    current_step INT DEFAULT 1,
    status ENUM('active','paused','completed') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_status (status)
);

CREATE TABLE session_state (
    session_id VARCHAR(64) PRIMARY KEY,
    data_json JSON NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
