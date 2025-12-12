from flask import Flask, render_template, session
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Needed because index() uses session

@app.route('/')
def index():
    # Generate a unique session ID for this tab/client
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(8)
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1000, debug=True)
