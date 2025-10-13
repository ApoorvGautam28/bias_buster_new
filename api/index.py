# Vercel Python entrypoint to serve the Flask app as a Serverless Function
# Exposes a WSGI callable `app` for Vercel

from app import app as application

# Vercel will look for a variable named `app`
app = application
