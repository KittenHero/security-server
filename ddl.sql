CREATE TABLE IF NOT EXISTS login (
	user_id INTEGER PRIMARY KEY AUTOINCREMENT,
	username VARCHAR(32) UNIQUE NOT NULL,
	hashedpwd BYTE(64) NOT NULL,
	salt VARCHAR(8,16) NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
	user_id INTEGER PRIMARY KEY,
	medicare_id VARCHAR UNIQUE,
  FOREIGN KEY (user_id) REFERENCES login(user_id)
);
CREATE TABLE IF NOT EXISTS medical_professionals (
	user_id INTEGER PRIMARY KEY,
	FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE TABLE IF NOT EXISTS staff (
	user_id INTEGER PRIMARY KEY,
	FOREIGN KEY (user_id) REFERENCES login(user_id)
);
CREATE TABLE IF NOT EXISTS admin (
	user_id INTEGER PRIMARY KEY,
	FOREIGN KEY(user_id) REFERENCES login(user_id)
);

CREATE TABLE IF NOT EXISTS medical_record (
	record_id INTEGER PRIMARY KEY AUTOINCREMENT,
	created_at VARCHAR DEFAULT (date('now')),
	user_id INTEGER NOT NULL,
	summary VARCHAR,
	details VARCHAR,
	recorded_by INTEGER NOT NULL,
	FOREIGN KEY (user_id) REFERENCES users(user_id),
	FOREIGN KEY (recorded_by) REFERENCES medical_professionals(user_id)
);

CREATE TABLE IF NOT EXISTS prescriptions (
	prescription_id INTEGER PRIMARY KEY AUTOINCREMENT,
	user_id INTEGER NOT NULL,
	date_prescribed VARCHAR DEFAULT (date('now')),
	medication VARCHAR,
	dosage VARCHAR,
	frequency VARCHAR,
	time VARCHAR,
	prescribed_by INTEGER NOT NULL,
	FOREIGN KEY (user_id) REFERENCES users(user_id),
	FOREIGN KEY (prescribed_by) REFERENCES medical_professionals(user_id)
);

CREATE TABLE IF NOT EXISTS rebate_requests (
	request_id INTEGER PRIMARY KEY AUTOINCREMENT,
	user_id INTEGER NOT NULL,
	amount INTEGER DEFAULT 0,
	reason VARCHAR NOT NULL,
	request_date VARCHAR DEFAULT (date('now')),
	approved BOOLEAN,
	processed_by INTEGER,
	date_processed VARCHAR,
	FOREIGN KEY (user_id) REFERENCES users(user_id),
	FOREIGN KEY (processed_by) REFERENCES staff(user_id)
);
