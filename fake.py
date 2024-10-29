
# # Route to add/edit user
# @app.route('/add_edit_user', methods=['POST'])
# def add_edit_user():
#     if 'admin_id' in session and request.method == 'POST':
#         stid = request.form.get('stid')
#         fname = request.form.get('fname')
#         lname = request.form.get('lname')
#         gender = request.form.get('gender')
#         contact = request.form.get('contact')
#         email = request.form.get('email')
        
#         cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#         if stid and fname and lname and gender and contact and email:
#             query = """
#                 INSERT INTO users (stid, fname, lname, gender, contact, email)
#                 VALUES (%s, %s, %s, %s, %s, %s)
#             """
#             values = (stid, fname, lname, gender, contact, email)
#             try:
#                 cursor.execute(query, values)
#                 mysql.connection.commit()
#                 flash('User added successfully!', 'success')
#             except MySQLdb.ProgrammingError as e:
#                 flash(f'Error adding user: {e}', 'danger')
#         else:
#             flash('All fields are required!', 'warning')
        
#         return redirect(url_for('manage_users'))
#     return redirect(url_for('admin_login'))

# # Route to manage users
# @app.route('/manage_users')
# def manage_users():
#     if 'admin_id' in session:
#         cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#         cursor.execute('SELECT * FROM users')
#         users = cursor.fetchall()
        
#         return render_template('manage_users.html', users=users)
#     return redirect(url_for('admin_login'))

# if __name__ == '__main__':
#     app.run(debug=True)
