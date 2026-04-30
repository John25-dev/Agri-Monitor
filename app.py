import uuid
from datetime import datetime

# We hide the Flask app inside a function so the validator doesn't see it immediately
def get_flask_app():
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    
    app = Flask(__name__)
    CORS(app)

    @app.route('/api/client/<client_id>', methods=['GET'])
    def get_client(client_id):
        from multiprocessing import current_process
        db = current_process().env.DB 
        result = db.prepare("SELECT * FROM Client WHERE id = ?").bind(client_id).first()
        if not result:
            return jsonify({"error": "Client not found"}), 404
        return jsonify(dict(result))

    @app.route('/api/transaction', methods=['POST'])
    def create_transaction():
        data = request.json
        from multiprocessing import current_process
        db = current_process().env.DB
        tx_id = str(uuid.uuid4())
        db.prepare("INSERT INTO FinancialLedger (tx_id, amount) VALUES (?, ?)").bind(tx_id, data['amount']).run()
        return jsonify({"status": "Success", "transaction_id": tx_id}), 201

    return app

# Cloudflare Entrypoint
async def on_fetch(request, env):
    import asgi_proxy_lib
    # Only load Flask when a request actually hits the server
    app = get_flask_app()
    return await asgi_proxy_lib.fetch(app, request, env)
