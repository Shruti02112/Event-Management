from flask import Flask, render_template, request, redirect, url_for, session 
import MySQLdb
from MySQLdb.cursors import DictCursor

app = Flask(__name__)
app.secret_key = 'your_secret_key'  

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '$hr0211',  
    'database': 'event_db'
}

def get_db_connection():
    return MySQLdb.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        db=db_config['database']
    )

@app.route('/')
def index():
    return render_template('homepg.html')

# Route for signup form
@app.route('/signup',  methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form['contact']
        organization = request.form['organization']

        conn = get_db_connection()
        cursor = conn.cursor()
        query = "INSERT INTO organizer (name, email, cont, org_name) VALUES (%s, %s, %s, %s)"
        values = (name, email, contact, organization)
        cursor.execute(query, values)
        conn.commit()
        org_id = cursor.lastrowid  
        session['org_id'] = org_id  
        cursor.close()
        conn.close()

        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        contact = request.form['contact']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the user exists in the database
            query = "SELECT * FROM organizer WHERE email = %s AND cont = %s"
            cursor.execute(query, (email, contact))
            user = cursor.fetchone()

            if user:
                # Store user session details
                session['email'] = user[2]
                session['org_id'] = user[0]   
                return redirect(url_for('addevent'))
            else:
                return "Invalid credentials. Please try again."

        except Exception as e:
            print(f"An error occurred: {e}")
            return redirect(url_for('error'))
        finally:
            cursor.close()
            conn.close()

    elif request.method == 'GET':
        email = request.args.get('email')
        contact = request.args.get('contact')

        if email and contact:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                # Check if the user exists in the database
                query = "SELECT * FROM organizer WHERE email = %s AND cont = %s"
                cursor.execute(query, (email, contact))
                user = cursor.fetchone()

                if user:
                    session['org_id'] = user[0] 
                    session['email'] = user[2]  
                    return redirect(url_for('addevent'))
                else:
                    return "Invalid credentials. Please try again."

            except Exception as e:
                print(f"An error occurred: {e}")
                return redirect(url_for('error'))
            finally:
                cursor.close()
                conn.close()

    return render_template('login.html')

# Route for adding events
@app.route('/addevent', methods=['GET', 'POST'])
def addevent():
    if request.method == 'POST':
        event_name = request.form['eventName']
        event_date = request.form['eventDate']
        event_time = request.form['eventTime']
        event_location = request.form['eventLocation']
        event_description = request.form['eventDescription']
        org_id = session.get('org_id')  

        if not org_id:
            return redirect(url_for('error'))  

        conn = get_db_connection()
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO event (eve_name, eve_date, loc, time, des, org_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (event_name, event_date, event_location, event_time, event_description, org_id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('logout'))

    return render_template('addevent.html')

#Routing for homepage
@app.route('/homepg')
def homepg():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM event ORDER BY event_id DESC")
        events_data = cursor.fetchall()  

        # Convert fetched data into a list of dictionaries
        events = []
        for row in events_data:
            events.append({
                'event_id': row[0],
                'eve_name': row[1],
                'eve_date': row[2],
                'loc': row[3],
                'time': row[4],
                'des': row[5],
                'total': row[6]
            })

        return render_template('homepg.html', events=events)

    except Exception as e:
        app.logger.error(f"Error fetching events: {e}")  
        return "An error occurred while fetching events.", 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

#route for log
@app.route('/log', methods=['GET', 'POST'])
def log():
    if request.method == 'POST':
        email = request.form['email']
        contact = request.form['contact']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the user exists in the database
            query = "SELECT * FROM organizer WHERE email = %s AND cont = %s"
            cursor.execute(query, (email, contact))
            user = cursor.fetchone()

            if user:
                # Store user session details
                session['org_id'] = user[0] 
                session['email'] = user[2]  
                return redirect(url_for('addevent'))
            else:
                return "Invalid credentials. Please try again."

        except Exception as e:
            print(f"An error occurred: {e}")
            return redirect(url_for('error'))
        finally:
            cursor.close()
            conn.close()

    elif request.method == 'GET':
        email = request.args.get('email')
        contact = request.args.get('contact')

        if email and contact:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                # Check if the user exists in the database
                query = "SELECT * FROM organizer WHERE email = %s AND cont = %s"
                cursor.execute(query, (email, contact))
                user = cursor.fetchone()

                if user:
                    # Store user session details
                    if user:
   
                        session['org_id'] = user[0] 
                        session['email'] = user[2]  # Assuming 2nd column is email
                    return redirect(url_for('show_events'))
                else:
                    return "Invalid credentials. Please try again."

            except Exception as e:
                print(f"An error occurred: {e}")
                return redirect(url_for('error'))
            finally:
                cursor.close()
                conn.close()


    return render_template('log.html')

#Route For event management
@app.route('/event_management', defaults={'org_id': None})
@app.route('/event_management/<int:org_id>')
def show_events(org_id):
    db = get_db_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    if org_id is None:
        org_id = session.get('org_id')  
        app.logger.info(f"Fetched org_id from session: {org_id}")

    if org_id:
        cursor.execute('SELECT * FROM event WHERE org_id = %s', (org_id,))
        events = cursor.fetchall()
        app.logger.info(f"Events fetched for org_id: {org_id}")
    else:
        return "No organization ID found.", 404

    cursor.close()
    db.close()

    return render_template('event_management.html', events=events)

#Route for participants list
@app.route('/participants/<int:event_id>')
def participant_list(event_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT reg_name, reg_email FROM reg WHERE eve_id = %s", (event_id,))
        participants_data = cursor.fetchall()  

        participants = []
        for row in participants_data:
            participants.append({
                'reg_name': row[0],
                'reg_email': row[1],
            })

        return render_template('participant_list.html', participants=participants, event_id=event_id)

    except Exception as e:
        app.logger.error(f"Error fetching participants for event {event_id}: {e}")  # Log the error
        return "An error occurred while fetching participants.", 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/end_event/<int:event_id>')
def end_event(event_id):
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute('DELETE FROM event WHERE event_id = %s', (event_id,))

    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('show_events'))

#Route for update
@app.route('/update/<int:event_id>', methods=['GET', 'POST'])
def update(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        event_name = request.form['eventName']
        event_date = request.form['eventDate']
        event_time = request.form['eventTime']
        event_location = request.form['eventLocation']
        event_description = request.form['eventDescription']

        query = """
            UPDATE event 
            SET eve_name = %s, eve_date = %s, time = %s, loc = %s, des = %s
            WHERE event_id = %s
        """
        cursor.execute(query, (event_name, event_date, event_time, event_location, event_description, event_id))
        conn.commit()
        
        return redirect(url_for('show_events')) 
    
    cursor.execute("SELECT * FROM event WHERE event_id = %s", (event_id,))
    event = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('update.html', event=event)

#Route for event registration
@app.route('/register', methods=['POST'])
def register():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        event_id = request.form.get('event_id')

        print(f"Received data: Name: {name}, Email: {email}, Event ID: {event_id}")  

        if not name or not email or not event_id:
            return "All fields are required.", 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("INSERT INTO reg (reg_name, reg_email, eve_id) VALUES (%s, %s, %s)", (name, email, event_id))
        conn.commit()

        return "Registration successful!", 201

    except Exception as e:
        print(f"An error occurred: {e}")  
        return "An error occurred during registration.", 500  

    finally:
        if 'cursor' in locals() and 'conn' in locals():
            cursor.close()
            conn.close()
            
#Route to display ticket
@app.route('/tickets', defaults={'reg_id': None})
@app.route('/tickets/<int:reg_id>')
def tickets(reg_id):
    if reg_id is None:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT MAX(reg_id) FROM reg")
        latest_reg_id = cursor.fetchone()

        if latest_reg_id:
            reg_id = latest_reg_id[0]  
        else:
            return "No registrations found", 404

        cursor.close()
        conn.close()

    app.logger.info(f"Fetching ticket for reg_id: {reg_id}")  # Log the reg_id
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.reg_name, r.reg_email, e.eve_name, e.eve_date, e.loc, e.time
        FROM reg r
        JOIN event e ON r.eve_id = e.event_id
        WHERE r.reg_id = %s
    """, (reg_id,))

    registration = cursor.fetchone()
    cursor.close()
    conn.close()

    if registration:
        return render_template('ticket.html', registration=registration)
    else:
        return "Ticket not found", 404

 # Clear session data   
@app.route('/logout')
def logout():
    session.pop('org_id', None)  
    session.pop('email', None)   
    return redirect(url_for('homepg'))  

if __name__ == "__main__":
    app.run(debug= True)
