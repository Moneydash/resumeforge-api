from flask import Flask, jsonify
from flask_cors import CORS

from api.routes.v1.pdf import generate_bp

def create_app():
    app = Flask(__name__)

    try:
        CORS(app, resources={r'/*': {'origins': '*'}})
    except Exception as e:
        print(f"Error initializing extensions: {str(e)}")
        raise

    @app.route("/check")
    def check():
        return jsonify({'status': 'okay'}), 200
        
    # Register blueprints
    app.register_blueprint(generate_bp, url_prefix='/v1/api/pdf')

    return app

if __name__ == '__main__':
    try:
        app = create_app()
        port = 5000
        host = '0.0.0.0'

        app.run(host=host, port=port, debug=True)
    except Exception as e:
        print(f"Failed to start application: {str(e)}")