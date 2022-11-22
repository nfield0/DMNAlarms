DROP DATABASE IF EXISTS DMN_Alarms;
CREATE DATABASE DMN_Alarms;

USE DMN_Alarms;
/*DROP TABLES IF EXISTS employee_table, employee_access_table, face_table, */

CREATE TABLE fingerprint_table(
fingerprint_id INT NOT NULL AUTO_INCREMENT,
fingerprint_image BLOB(255) NOT NULL,
PRIMARY KEY(fingerprint_id));

CREATE TABLE admin(
    adminId INT NOT NULL AUTO_INCREMENT,
    adminEmail VARCHAR(250) NOT NULL,
    adminPassword VARCHAR(30) NOT NULL ,
    PRIMARY KEY(adminId));

/*WORKING TITLE IF YOUS HAVE A BETTER NAME PLEASE DONT HESITATE TO CHANGE IT :)*/
CREATE TABLE face_table(
face_id INT NOT NULL AUTO_INCREMENT,
face_image BLOB(255) NOT NULL,
PRIMARY KEY(fingerprint_id));

CREATE TABLE employee_table(
employee_id INT NOT NULL AUTO_INCREMENT,
employee_firstname VARCHAR (20) NOT NULL,
employee_surname VARCHAR (30) NOT NULL, 
employee_email VARCHAR (50) NOT NULL,
face_test BLOB NOT NULL, /*Change back to relational*/
img_filename varchar(50) NOT NULL, /*Change back to relational*/
PRIMARY KEY(employee_id));


/*Only needed if you havent dropped it yet hence wht it is commented out*/
/*ALTER TABLE employee_table
DROP fingerprint_test;*/

ALTER TABLE employee_table
ADD fingerprint INT NOT NULL;

UPDATE employee_table SET fingerprint = 10 WHERE employee_id = 5;

CREATE TABLE employee_access_table(
access_id INT NOT NULL AUTO_INCREMENT,
employee_access_date DATE,
employee_access_time TIME,
employee_id INT NOT NULL,
PRIMARY KEY(access_id),
FOREIGN KEY(employee_id) REFERENCES employee_table(employee_id));

ALTER TABLE employee_table
ADD fingerprint INT NOT NULL;

UPDATE employee_table SET fingerprint = 10 WHERE employee_id = 5;

CREATE TABLE door_records_tables(
door_id INT NOT NULL AUTO_INCREMENT,
access_id INT NOT NULL,
door_status VARCHAR (10) NOT NULL,
PRIMARY KEY(door_id),
FOREIGN KEY(access_id) REFERENCES access_id(access_table));

CREATE TABLE motion(
motion_id INT NOT NULL AUTO_INCREMENT,
motion_date DATE,
motion_time TIME,
PRIMARY KEY(motion_id));


/*Dummy Data*/

/*Query for logging the fingerprint*/
SELECT ac.access_id, emp.employee_firstname, ac.employee_access_date, ac.employee_access_time
FROM employee_access_table
INNER JOIN employee_table ON employee_access_table.employee_id = employee_table.employee_id;



/***********/

/*Very basic queries that get all the data from each table*/
SELECT * FROM fingerprint_table;
SELECT * FROM face_table;
SELECT * FROM employee_table;
SELECT * FROM employee_acces_table;
SELECT * FROM door_records_tables;
SELECT * FROM motion;

/*Trigger that splits the data into the separate tables*/
DROP TRIGGER IF EXISTS multiAdd;
CREATE TRIGGER multiAdd
AFTER INSERT ON employee_table
FOR EACH ROW 
BEGIN
INSERT INTO fingerprint_table values(fingerprint_id, fingerprint_image);
INSERT INTO face_table values(face_id, face_image);
END


