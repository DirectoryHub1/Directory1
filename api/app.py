import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    print("Flask app is running and / route accessed!")
    return "Hello from Flask!"

@app.route('/api/test')
def api_test():
    print("API test route accessed!")
    return {"message": "API is working!"}

# No app.run() here for Vercel deployment
