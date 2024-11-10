CREATE TABLE IF NOT EXISTS residents (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    dob DATE,
    nationality VARCHAR(100),
    remarks VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO residents (first_name, last_name, dob, nationality, remarks) VALUES
('Koumudi', 'Ganepola', '1995-07-30', 'Sri Lanka', 'Test'),
('Ahmad', 'Ahmad', '1996-12-05', 'Bangladesh', 'Test'),
('Paul', 'Hart', '1989-01-12', 'Hungary', 'Test'),
('Melissa', 'Reese', '2001-10-19', 'Iceland', 'Test');