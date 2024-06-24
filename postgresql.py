from flask import Flask, request, jsonify
import psycopg2
from psycopg2 import sql

app = Flask(__name__)

# Database connection parameters
DB_HOST = "localhost"
DB_NAME = "postgres"
DB_USER = "nitin"
DB_PASS = "Nitin@123"

def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    return conn

@app.route('/create_table', methods=['POST'])
def create_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS medical_records (
            id SERIAL PRIMARY KEY,
            patient_name VARCHAR(100),
            condition VARCHAR(100),
            treatment VARCHAR(100),
            doctor_name VARCHAR(100)
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()
    return 'Table created successfully!', 200

@app.route('/add_record', methods=['POST'])
def add_record():
    data = request.get_json()
    patient_name = data.get('patient_name')
    condition = data.get('condition')
    treatment = data.get('treatment')
    doctor_name = data.get('doctor_name')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        sql.SQL("INSERT INTO medical_records (patient_name, condition, treatment, doctor_name) VALUES (%s, %s, %s, %s)"),
        [patient_name, condition, treatment, doctor_name]
    )
    conn.commit()
    cur.close()
    conn.close()
    return 'Record added successfully!', 201

if __name__ == '__main__':
    app.run(debug=True)

