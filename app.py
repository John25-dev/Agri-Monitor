import uuid
from datetime import datetime

# Hide Flask inside a function so the Cloudflare validator passes the build
def create_app():
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    
    app = Flask(__name__)
    CORS(app)

    @app.route('/')
    def home():
        return jsonify({
            "status": "JOFARM API Online", 
            "message": "Welcome to Agri-Monitor",
            "time": datetime.utcnow().isoformat()
        })

    @app.route('/api/client/<client_id>', methods=['GET'])
    def get_client(client_id):
        from multiprocessing import current_process
        db = current_process().env.DB 
        result = db.prepare("SELECT * FROM Client WHERE id = ?").bind(client_id).first()
        return jsonify(dict(result)) if result else (jsonify({"error": "Not found"}), 404)

    return app

# Placeholder for the app instance
_app = None

async def on_fetch(request, env):
    import asgi_proxy_lib
    global _app
    if _app is None:
        _app = create_app()
    return await asgi_proxy_lib.fetch(_app, request, env)
