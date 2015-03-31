# all the imports
import sqlite3
from contextlib import closing

from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from twilio.rest import TwilioRestClient
import twilio.twiml

# configuration
DATABASE = '/tmp/heatr.db'
DEBUG = True
SECRET_KEY = '' 
USERNAME = ''
PASSWORD = ''

# Twilio account credentials
account_sid = ""
auth_token  = ""
client = TwilioRestClient(account_sid, auth_token)

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/')
def show_entries():
    cur = g.db.execute('select mode, temperature, fan from entries order by id desc')
    entries = [dict(mode=row[0], temperature=row[1], fan=row[2]) for row in cur.fetchmany(1)]

    cur2 = g.db.execute('select response from responses order by id desc')
    responses = [dict(response=row[0]) for row in cur2.fetchmany(1)]
    return render_template('show_entries.html', entries=entries, responses=responses)

@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    mode = request.form.get('mode')
    temperature = request.form.get('temperature')
    fan = request.form.get('fan')

    g.db.execute('insert into entries (mode, temperature, fan) values (?, ?, ?)',
                [mode, temperature, fan])
    g.db.commit()
    print 'done db commit'

    sms_input = mode + ' ' + temperature + ' ' + fan
    print sms_input
    message = client.messages.create(body=sms_input,
    to="",    # Replace with your phone number
    from_="") # Replace with your Twilio number
    print message
    flash('SMS with new settings was successfully posted','sms_input')

    #return redirect(url_for('show_incoming'))
    return redirect(url_for('show_entries'))

# new route 
@app.route('/incoming', methods=['GET'])
def handle_incoming():
    message = request.values.get('Body')
    print message 
    #return redirect(url_for('show_incoming'), messagebody=message)
    #return redirect(url_for('show_entries'))
    g.db.execute('insert into responses (response) values (?)',
                [message])
    g.db.commit()
    print 'done db commit'

    return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5050)
