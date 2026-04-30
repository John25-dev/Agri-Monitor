import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- ROUTES ---

@app.route('/')
def home():
    return jsonify({"status": "JOFARM API Online", "time": datetime.utcnow().isoformat()})

@app.route('/api/client/<client_id>', methods=['GET'])
def get_client(client_id):
    from multiprocessing import current_process
    # Accessing the D1 Database binding
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
    
    # Simple insert to verify database connection
    db.prepare("INSERT INTO FinancialLedger (tx_id, amount) VALUES (?, ?)").bind(
        tx_id, data.get('amount', 0)
    ).run()
    
    return jsonify({"status": "Success", "transaction_id": tx_id}), 201

# --- CLOUDFLARE ENTRYPOINT ---

async def on_fetch(request, env):
    # This library was successfully installed in your last log
    import asgi_proxy_lib
    return await asgi_proxy_lib.fetch(app, request, env)
