import sqlite3
from flask import Flask, request, jsonify, abort


app = Flask(__name__)


# Database connection function
def db_connection():
    conn = None
    try:
        conn = sqlite3.connect("park.db")
    except sqlite3.Error as e:
        print(e)
    return conn

def history_add(date, name, place, vin, take):
    conhistory = sqlite3.connect('history.db')
    cursothistory = conhistory.cursor()

    cursothistory.execute("INSERT INTO history (Date, Name, Place, Vin, Take) VALUES (?, ?, ?, ?, ?)",
                          (date, name, place, vin, take))
    conhistory.commit()
    conhistory.close()
    print("Data added to history.db")


@app.route('/')
def index():
    return 'Hello, park'


@app.route('/user', methods=['GET', 'POST'])
def users():
    conusers = sqlite3.connect('user.db')
    cusers = conusers.cursor()

    if request.method == 'GET':
        cusers.execute('SELECT * FROM user')
        users = cusers.fetchall()

        return jsonify(users)

    if request.method == 'POST':
        try:
            new_name = request.form['name']
            new_psw = request.form['psw']

            cusers.execute("""
                INSERT INTO user(Name, Psw)
                VALUES(?, ?)
                """, (new_name, new_psw))
            conusers.commit()  # Don't forget to commit the transaction after insertion

            # Fetch the last inserted row ID
            new_user_id = cusers.lastrowid

            return jsonify({"user": f'{new_user_id, new_name, new_psw}'})

        except Exception as e:
            return jsonify({'error': str(e)}), 400

    return jsonify({'error': 'Invalid request method'}), 405


@app.route('/parks', methods=['GET', 'POST'])
def park_all():
    conn = db_connection()
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute("SELECT * FROM park")
        parks = cursor.fetchall()

        grouped_parks = {}
        for park in parks:
            first_char = park[1][0]  # Get the first character of the place name
            if first_char not in grouped_parks:
                grouped_parks[first_char] = []
            grouped_parks[first_char].append({'Place': park[1], 'Busy': park[2], 'Vin': park[3]})

        return jsonify(grouped_parks)

    return jsonify({'error': 'Invalid request method'}), 405


@app.route('/get_place', methods=['GET'])
def sent_place():
    conn = db_connection()
    cursor = conn.cursor()

    if request.method == "GET":
        try:
            car_vin = request.form['vin']  # Use request.args.get() for query parameters

            cursor.execute("SELECT Place FROM park WHERE Busy = ?", ('free',))
            places = cursor.fetchall()

            if len(places) == 0:
                return jsonify({"message": "no place"})

            # Select the last available place
            place = places[-1][0]

            # Assign the parking place to the car
            cursor.execute("UPDATE park SET Vin = ? ,Busy = ? WHERE Place = ?",
                           (car_vin,'temp', place))
            conn.commit()
            conn.close()
            return jsonify({'Place': place})

        except Exception as e:
            return jsonify({'error': str(e)}), 400

    return jsonify({'error': 'Invalid request method'}), 405


@app.route('/post_place', methods=['POST'])
def check_place():
    conn = db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        try:
            new_place = request.form['place']
            new_vin = request.form['vin']
            new_date = request.form['date']
            new_userid = request.form['usrid']

            cursor.execute("SELECT Vin FROM park WHERE Place = ?", (new_place,))
            places = cursor.fetchone()  # Fetch a single row
            print(places)

            if places and new_vin == places[
                0]:  # Check if places is not None and compare new_vin with the VIN from places
                cursor.execute("UPDATE park SET Vin = ?, Busy = ? WHERE Place = ?",
                               (new_vin, 'yes', new_place))
                conn.commit()

                history_add(new_date, new_userid, new_place, new_vin, 1)  # Assuming new_date is a datetime object

                return jsonify({'message': f'Updated: {new_place}, yes, {new_vin}'})

            else:
                return jsonify({'error': f'Invalid VIN for place: {new_place}'})

        except Exception as e:
            return jsonify({'error': str(e)}), 400

    return jsonify({'error': 'Invalid request method'}), 405


@app.route('/goout_place', methods=['POST'])
def goout_place():
    conn = db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        try:

            new_vin = request.form['vin']
            new_date = request.form['date']
            new_userid = request.form['usrid']

            cursor.execute("SELECT * FROM park WHERE Vin = ?", (new_vin,))
            place = cursor.fetchone()

            new_place = place[1]

            if new_vin == place[3]:  # Check if place exists and VIN matches
                cursor.execute("UPDATE park SET Vin = ?, Busy = ? WHERE Vin = ?",
                               ("free", "free", new_vin))
                conn.commit()

                history_add(new_date, new_userid, new_place, new_vin, 0)  # Assuming new_date is a datetime object

                return jsonify({'message': f'Updated: {new_place}, free, {new_vin}'})

            else:
                return jsonify({'error': f'No car with VIN {new_vin} found at place {new_place}'})

        except Exception as e:
            return jsonify({'error': str(e)}), 400

    return jsonify({'error': 'Invalid request method'}), 405



if __name__ == '__main__':
    app.run(debug=True , port=5001)