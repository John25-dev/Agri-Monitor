import uuid
from datetime import datetime

# Move Flask imports INSIDE the entry point or functions to avoid early crashes
def create_app():
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    
    app = Flask(__name__)
    CORS(app)

    @app.route('/api/client/<client_id>', methods=['GET'])
    def get_client(client_id):
        from multiprocessing import current_process
        db = current_process().env.DB 
        result = db.prepare("SELECT * FROM Client WHERE id = ?").bind(client_id).first()
        return jsonify(dict(result)) if result else (jsonify({"error": "Not found"}), 404)

    return app

app = create_app()

async def on_fetch(request, env):
    import asgi_proxy_lib
    return await asgi_proxy_lib.fetch(app, request, env)
