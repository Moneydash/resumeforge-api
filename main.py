import os
from flask import Flask, jsonify
from flask_cors import CORS
from upstash_redis import Redis
from dotenv import load_dotenv

from api.routes.galaxy.pdf import generate_bp

load_dotenv()

def create_app():
    app = Flask(__name__)

    token = os.getenv('UPSTASH_REDIS_TOKEN')
    if not token:
        raise ValueError("UPSTASH_REDIS_TOKEN environment variable is required")
    
    redis_url = 'https://ace-pegasus-31891.upstash.io'
    
    redis_client = Redis(redis_url, token)

    # attach redis into the app
    app.redis_client = redis_client

    try:
        CORS(app, resources={r'/*': {'origins': '*'}})
    except Exception as e:
        print(f"Error initializing extensions: {str(e)}")
        raise

    @app.route("/check")
    def check():
        return jsonify({'status': 'okay'}), 200
        
    # Register blueprints
    app.register_blueprint(generate_bp, url_prefix='/galaxy/api/pdf')

    return app

if __name__ == '__main__':
    try:
        app = create_app()
        port = 5000
        host = '0.0.0.0'

        app.run(host=host, port=port, debug=True)
    except Exception as e:
        print(f"Failed to start application: {str(e)}")