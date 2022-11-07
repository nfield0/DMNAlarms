/*DROP DATABASE DMN_Alarms;*/
CREATE DATABASE DMN_Alarms;

/*USE DATABASE DMN_Alarms;*/
/*DROP TABLES IF EXISTS employee_table, employee_access_table, face_table, */

CREATE TABLE fingerprint_table(
fingerprint_id INT NOT NULL AUTO_INCREMENT,
fingerprint_image VARCHAR (255) NOT NULL,
PRIMARY KEY(fingerprint_id));


/*WORKING TITLE IF YOUS HAVE A BETTER NAME PLEASE DONT HESITATE TO CHANGE IT :)*/
CREATE TABLE face_table(
face_id INT NOT NULL AUTO_INCREMENT,
face_image VARCHAR (255) NOT NULL,
PRIMARY KEY(fingerprint_id));



CREATE TABLE employee_table(
employee_id INT NOT NULL AUTO_INCREMENT,
employee_firstname VARCHAR (20) NOT NULL,
employee_surname VARCHAR (30) NOT NULL, 
employee_email VARCHAR (50) NOT NULL,
fingerprint_id INT NOT NULL,
face_id INT NOT NULL,
PRIMARY KEY(employee_id),
FOREIGN KEY(fingerprint_id) REFERENCES fingerprint_table(fingerprint_id),
FOREIGN KEY(face_id) REFERENCES face_table(face_id));


CREATE TABLE employee_access_table(
access_id INT NOT NULL AUTO_INCREMENT,
employee_access_date DATE,
employee_access_time TIME,
employee_id INT NOT NULL,
PRIMARY KEY(access_id),
FOREIGN KEY(employee_id) REFERENCES employee_table(employee_id));


CREATE TABLE door_records_tables(
door_id INT NOT NULL AUTO_INCREMENT,
access_id INT NOT NULL,
door_status VARCHAR (10) NOT NULL,
PRIMARY KEY(door_id),
FOREIGN KEY(access_id) REFERENCES access_id(access_table));

CREATE TABLE motion(
motion_id INT NOT NULL AUTO_INCREMENT,
motion_date DATE,
motion_time TIME
);


/*Very basic queries that get all the data from each table*/
SELECT * FROM fingerprint_table;
SELECT * FROM face_table;
SELECT * FROM employee_table;
SELECT * FROM employee_acces_table;
SELECT * FROM door_records_tables;
SELECT * FROM motion;



