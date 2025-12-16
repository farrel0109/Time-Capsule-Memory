# BabyGrow Application Entry Point
import os
from app import create_app

# Create the Flask application
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Run the development server
    app.run(
        debug=True,
        host='127.0.0.1',
        port=5001
    )
