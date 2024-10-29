from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, Response
import json
import random
from flask_mysqldb import MySQL
import MySQLdb.cursors
import subprocess
import random
import json
from nltk_utils import bag_of_words, tokenize, stem

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'loyaltvukreationz'

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'campus'

mysql = MySQL(app)

# Helper function to read data from JSON file
def read_intents():
    json_file = 'intents.json'
    try:
        with open(json_file, 'r') as f:
            intents = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        intents = {'intents': []}
        write_intents(intents)  # Create a new JSON file with empty intents list
    return intents

# Helper function to write data to JSON file
def write_intents(intents):
    json_file = 'intents.json'
    with open(json_file, 'w') as f:
        json.dump(intents, f, indent=2)

# Middleware to check if user is logged in before accessing specific routes
@app.before_request
def require_login():
    allowed_routes = ['index', 'user_login', 'admin_login', 'static', 'chat', 'logout']  # Add 'static' for static files like CSS, JS
    if request.endpoint not in allowed_routes:
        if request.endpoint in ['chatroom', 'chat'] and 'loggedin' not in session:
            return redirect(url_for('user_login'))
        elif request.endpoint in ['admin_panel', 'update_admin_password', 'view_intents', 'add_intent', 'update_intent', 'delete_intent', 'train_chatbot', 'manage_users', 'add_user', 'edit_user'] and 'admin_id' not in session:
            return redirect(url_for('admin_login'))


# Route to home page (index)
@app.route('/')
def index():
    return render_template('index.html')

# Route to home page (keep)
@app.route('/keep')
def keep():
    return render_template('keep.html')

# Route to home page (test)
@app.route('/test')
def test():
    return render_template('test.html')

# Route to home page (text)
@app.route('/text')
def text():
    return render_template('text.html')


# Route to train page (train)
@app.route('/train')
def train():
    return render_template('train.html') 

# Route to home page (index)
@app.route('/home')
def home():
    return render_template('home.html')


# Route to handle user login
@app.route('/user_login', methods=['POST'])
def user_login():
    if 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE fname = %s AND stid = %s', (username, password,))
        account = cursor.fetchone()

        if account:
            session['loggedin'] = True
            session['id'] = account['stid']
            session['username'] = account['fname']
            return jsonify({'success': True, 'redirect_url': url_for('chatroom')})
        else:
            flash('Invalid username or password', 'error')
            return jsonify({'success': False, 'message': 'Invalid username or password'})
    return redirect(url_for('display_user_login'))


# Route for user dashboard (example)
@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        return 'Welcome, ' + session['username'] + '!'
    return redirect(url_for('index'))

# Route for admin login
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM admins WHERE username = %s AND password = %s', (username, password,))
        admin = cursor.fetchone()

        print(f"Admin record: {admin}")  # Debug print

        if admin:
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            return jsonify({'success': True, 'redirect_url': url_for('admin_panel')})
        else:
            flash('Invalid username or password. Please try again.', 'error')
            return jsonify({'success': False, 'message': 'Invalid username or password'})

    return render_template('admin_login.html')


# .................................ADMIN PANEL WORKS.....................................

# Route for admin panel
# Route for admin panel
@app.route('/admin_panel')
def admin_panel():
    if 'admin_id' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Count registered users
        cursor.execute('SELECT COUNT(*) AS user_count FROM users')
        user_count = cursor.fetchone()['user_count']
        
        # Count intents from the intents.json file
        intents = read_intents()
        intent_count = len(intents['intents'])
        
        # Count feedback messages
        cursor.execute('SELECT COUNT(*) AS feed_count FROM feedback')
        feed_count = cursor.fetchone()['feed_count']
        
        cursor.close()
        
        return render_template('admin_panel.html', user_count=user_count, intent_count=intent_count, feed_count=feed_count)
    else:
        return redirect(url_for('admin_login'))


# Route for updating admin password
@app.route('/update_admin_password', methods=['GET', 'POST'])
def update_admin_password():
    if 'admin_id' in session:
        if request.method == 'POST':
            current_password = request.form['current_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']

            # Validate the passwords
            if new_password != confirm_password:
                flash('New password and confirmation password do not match.', 'error')
            else:
                # Check if current password is correct
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM admins WHERE id = %s AND password = %s', (session['admin_id'], current_password))
                admin = cursor.fetchone()

                if admin:
                    # Update password
                    cursor.execute('UPDATE admins SET password = %s WHERE id = %s', (new_password, session['admin_id']))
                    mysql.connection.commit()
                    flash('Password updated successfully.', 'success')
                else:
                    flash('Incorrect current password.', 'error')

                cursor.close()

        return render_template('update_admin_password.html')
    return redirect(url_for('admin_login'))

# ....................... MANAGING INTENTS ..............................

# Function to load intents from JSON file
def load_intents():
    with open('intents.json', 'r') as f:
        intents_data = json.load(f)
    return intents_data['intents']

# Route to fetch all intents
@app.route('/view_intents')
@app.route('/fetch_intents')
def fetch_intents():
    intents = load_intents()
    return render_template('view_intents.html', intents=intents)

# Route to get a single intent by tag
@app.route('/get_intent/<tag>', methods=['GET'])
def get_intent(tag):
    intents = load_intents()
    for intent in intents:
        if intent['tag'] == tag:
            return jsonify({'success': True, 'intent': intent})
    return jsonify({'success': False, 'message': 'Intent not found'})

# Route to save or update an intent
@app.route('/save_intent', methods=['POST'])
def save_intent():
    tag = request.form.get('tag')
    patterns = [p.strip() for p in request.form.get('patterns').split(',')]
    responses = [r.strip() for r in request.form.get('responses').split(',')]

    intents = load_intents()

    # Check if intent already exists
    for intent in intents:
        if intent['tag'] == tag:
            intent['patterns'] = patterns
            intent['responses'] = responses
            flash(f'Intent "{tag}" updated successfully.', 'success')
            break
    else:
        new_intent = {
            'tag': tag,
            'patterns': patterns,
            'responses': responses
        }
        intents.append(new_intent)
        flash(f'New intent "{tag}" added successfully.', 'success')

    # Save updated intents back to JSON file
    with open('intents.json', 'w') as f:
        json.dump({'intents': intents}, f, indent=4)

    return redirect(url_for('fetch_intents'))

# Route to delete an intent
@app.route('/delete_intent/<tag>', methods=['POST'])
def delete_intent(tag):
    intents = load_intents()
    for intent in intents:
        if intent['tag'] == tag:
            intents.remove(intent)
            flash(f'Intent "{tag}" deleted successfully.', 'success')
            break

    # Save updated intents back to JSON file
    with open('intents.json', 'w') as f:
        json.dump({'intents': intents}, f, indent=4)

    return jsonify({'success': True})



# .........................TRAINING THE CHATBOT 1.................................

@app.route('/train_chatbot', methods=['POST'])
def train_chatbot():
    try:
        # Execute the training script
        result = subprocess.run(['python', 'train.py'], capture_output=True, text=True)
        if result.returncode == 0:
            return jsonify({"message": "Training successful", "details": result.stdout}), 200
        else:
            return jsonify({"message": "Training failed", "details": result.stderr}), 500
    except Exception as e:
        return jsonify({"message": "An error occurred", "details": str(e)}), 500
    


# .........................VIEWING AND MANAGING USERS ................................
#Route for fetching users
def fetch_users():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT stid, fname, lname, gender, contact, email FROM users')
    users = cursor.fetchall()
    cursor.close()
    return users


# Route for viewing users in a tabular format
@app.route('/view_users')
def view_users():
    if 'admin_id' in session:
        users = fetch_users()
        return render_template('view_users.html', users=users)
    return redirect(url_for('admin_login'))


# Route for adding a new user
@app.route('/add_user', methods=['POST'])
def add_user():
    if 'admin_id' in session:
        data = request.get_json()
        stid = data.get('stid')
        fname = data.get('fname')
        lname = data.get('lname')
        gender = data.get('gender')
        contact = data.get('contact')
        email = data.get('email')
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if data.get('user-index'):  # Update user
            cursor.execute('UPDATE users SET fname = %s, lname = %s, gender = %s, contact = %s, email = %s WHERE stid = %s',
                           (fname, lname, gender, contact, email, stid))
        else:  # Add new user
            cursor.execute('INSERT INTO users (stid, fname, lname, gender, contact, email) VALUES (%s, %s, %s, %s, %s, %s)',
                           (stid, fname, lname, gender, contact, email))
        mysql.connection.commit()
        cursor.close()

        return jsonify({'success': True, 'message': 'User added/updated successfully'})
    return jsonify({'success': False, 'message': 'Unauthorized access'})


# Route to update users
@app.route('/update_user/<int:stid>', methods=['GET'])
def update_user(stid):
    if 'admin_id' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT stid, fname, lname, gender, contact, email FROM users WHERE stid = %s', (stid,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            return jsonify({'success': True, 'user': user})
        else:
            return jsonify({'success': False, 'message': 'User not found.'}), 404
    else:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 401


# Route for editing an existing user
@app.route('/edit_user/<int:stid>', methods=['GET', 'POST'])
def edit_user(stid):
    if 'admin_id' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT stid, fname, lname, gender, contact, email FROM users WHERE stid = %s', (stid,))
        user = cursor.fetchone()
        cursor.close()

        if user:
            if request.method == 'POST':
                fname = request.form['fname']
                lname = request.form['lname']
                gender = request.form['gender']
                contact = request.form['contact']
                email = request.form['email']

                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('UPDATE users SET fname = %s, lname = %s, gender = %s, contact = %s, email = %s WHERE stid = %s', (fname, lname, gender, contact, email, stid))
                mysql.connection.commit()
                cursor.close()
                flash('User updated successfully.', 'success')
                return redirect(url_for('view_users'))

            return render_template('edit_user.html', user=user)
        else:
            flash('User not found.', 'error')
            return redirect(url_for('view_users'))
    
    return redirect(url_for('admin_login'))



# Route for deleting a user
@app.route('/delete_user/<int:stid>', methods=['POST'])
def delete_user(stid):
    if 'admin_id' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM users WHERE stid = %s', (stid,))
        mysql.connection.commit()
        cursor.close()
        flash('User deleted successfully.', 'success')
        return jsonify({'success': True, 'message': 'User deleted successfully'})
    
    return jsonify({'success': False, 'message': 'Unauthorized access'})



# ............................HANDLING CHAT MESSAGE.........................

# Route to handle chat messages
@app.route('/chat', methods=['POST'])
def chat():
    if 'loggedin' in session:
        message = request.json.get('message', '')
        response = get_response(message)
        return jsonify({'response': response})
    return jsonify({'error': 'Unauthorized access'}), 403

def get_response(message):
    intents = read_intents()
    for intent in intents['intents']:
        for pattern in intent['patterns']:
            if pattern.lower() in message.lower():
                return random.choice(intent['responses'])

    # Save the feedback as the bot doesn't understand the message
    if 'loggedin' in session:
        user_id = session['id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO feedback (user_id, message, response, status) VALUES (%s, %s, %s, %s)', 
                       (user_id, message, "Sorry, Our admin is currently crafting the perfect response to your query. They'll get back to you within the next 24 hours. Please check back later for their expert reply!In the meantime, feel free to ask another question. We're here to help!", 'unresolved'))
        mysql.connection.commit()
        cursor.close()
    return "Sorry, I don't have that information yet."


@app.route('/chatroom')
def chatroom():
    if 'loggedin' in session:
        return render_template('chatroom.html')
    else:
        flash('You need to log in first.', 'error')
        return redirect(url_for('user_login'))



# .............................. FEEDBACK ROUTES ..............................

# Route for submitting feedback
@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'loggedin' in session:
        user_id = session['id']
        message = request.json.get('message')
        response = get_response(message)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO feedback (user_id, message, response) VALUES (%s, %s, %s)', (user_id, message, response))
        mysql.connection.commit()
        cursor.close()

        return jsonify({'success': True, 'response': response, 'message': 'Feedback submitted successfully'})
    return jsonify({'success': False, 'message': 'Unauthorized access'})

# Route for viewing feedback
@app.route('/view_feedback')
def view_feedback():
    if 'admin_id' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT f.id, f.message, f.response, f.status, u.fname, u.lname FROM feedback f JOIN users u ON f.user_id = u.stid')
        feedback = cursor.fetchall()
        cursor.close()
        return render_template('view_feedback.html', feedback=feedback)
    return redirect(url_for('admin_login'))

# Route for resolving feedback
@app.route('/resolve_feedback/<int:feedback_id>', methods=['POST'])
def resolve_feedback(feedback_id):
    if 'admin_id' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE feedback SET status = %s WHERE id = %s', ('resolved', feedback_id))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True, 'message': 'Feedback resolved successfully'})
    return jsonify({'success': False, 'message': 'Unauthorized access'})


# Route for deleting feedback
@app.route('/delete_feedback/<int:feedback_id>', methods=['DELETE'])
def delete_feedback(feedback_id):
    if 'admin_id' in session:
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            # Check if feedback exists
            cursor.execute('SELECT * FROM feedback WHERE id = %s', (feedback_id,))
            feedback = cursor.fetchone()
            if feedback:
                cursor.execute('DELETE FROM feedback WHERE id = %s', (feedback_id,))
                mysql.connection.commit()
                cursor.close()
                return jsonify({'success': True, 'message': 'Feedback deleted successfully'})
            else:
                cursor.close()
                return jsonify({'success': False, 'message': 'Feedback not found'})
        except Exception as e:
            return jsonify({'success': False, 'message': 'An error occurred: ' + str(e)})
    return jsonify({'success': False, 'message': 'Unauthorized access'})

    # DELETING BULKY FEEDBACKS FROM THE DATA TABLE
@app.route('/delete_feedbacks', methods=['POST'])
def delete_feedbacks():
    if 'admin_id' in session:
        try:
            data = request.get_json()
            feedback_ids = data.get('ids', [])
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            for feedback_id in feedback_ids:
                cursor.execute('DELETE FROM feedback WHERE id = %s', (feedback_id,))
            mysql.connection.commit()
            cursor.close()
            return jsonify({'success': True, 'message': 'Selected feedback(s) deleted successfully'})
        except Exception as e:
            return jsonify({'success': False, 'message': 'An error occurred: ' + str(e)})
    return jsonify({'success': False, 'message': 'Unauthorized access'})



@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
