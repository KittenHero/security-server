CREATE TABLE IF NOT EXISTS login (
	user_id INTEGER PRIMARY KEY,
	username VARCHAR(32) UNIQUE NOT NULL,
	hashedpwd BYTE(64) NOT NULL,
	salt VARCHAR(8,16) NOT NULL,
);

CREATE TABLE IF NOT EXISTS users (
	user_id INTEGER FOREIGN KEY REFERENCES login(user_id),
	medicare_id VARCHAR UNIQUE,
	authorised BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE IF NOT EXISTS medical_professionals (
	user_id INTEGER PRIMARY KEY FOREIGN KEY REFERENCES users(user_id)
)
CREATE TABLE IF NOT EXISTS staff (
	user_id INTEGER PRIMARY KEY FOREIGN KEY REFERENCES login(user_id),
);
CREATE TABLE IF NOT EXISTS admin (
	user_id INTEGER PRIMARY KEY FOREIGN KEY REFERENCES login(user_id),
);

CREATE TABLE IF NOT EXISTS logs (
	log_id INTEGER PRIMARY KEY,
	subject INTEGER FOREIGN KEY REFERENCES login(user_id),
	action VARCHAR NOT NULL,
	object INTEGER FOREIGN KEY REFERENCES login(user_id)
);

CREATE TABLE IF NOT EXISTS medical_history (
	history_id INTEGER PRIMARY KEY,
	created_at VARCHAR DEFAULT date('now'),
	user_id INTEGER NOT NULL,
	summary VARCHAR,
	details VARCHAR,
	recorded_by INTEGER NOT NULL,
	CONSTRAINT valid_user FOREIGN KEY REFERENCES users(user_id),
	CONSTRAINT recorded_by_professional FOREIGN KEY
	recorded_by REFERENCES medical_professionals(user_id)
);

CREATE TABLE IF NOT EXISTS presciptions (
	presciption_id INTEGER PRIMARY KEY,
	user_id INTEGER NOT NULL,
	date_prescribed VARCHAR DEFAULT date('now'),
	medication VARCHAR,
	dosage VARCHAR,
	frequency VARCHAR,
	time VARCHAR,
	prescribed_by INTEGER NOT NULL,
	CONSTRAINT valid_user FOREIGN KEY user_id REFERENCES users(user_id),
	CONSTRAINT prescribed_by_profession FOREIGN KEY
	prescribed_by REFERENCES medical_professionals(user_id)
);

CREATE TABLE IF NOT EXISTS rebate_requests (
	request_id INTEGER PRIMARY KEY,
	user_id INTEGER NOT NULL,
	amount INTEGER DEFAULT 0,
	reason VARCHAR NOT NULL,
	request_date VARCHAR DEFAULT date('now'),
	approved BOOLEAN,
	processed_by INTEGER,
	date_processed VARCHAR,
	CONSTRAINT valid_user FOREIGN KEY user_id REFERENCES users(user_id),
	CONSTRAINT processed_by_staff FOREIGN KEY
	processed_by REFERENCES staff(user_id)
);
