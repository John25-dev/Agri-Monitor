import uuid
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- ROUTES ---

@app.route('/api/client/<client_id>', methods=['GET'])
def get_client(client_id):
    # 'env.DB' refers to your Cloudflare D1 database binding
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
    timestamp = datetime.utcnow().isoformat()

    db.prepare("""
        INSERT INTO FinancialLedger (tx_id, timestamp, payer_name, phone_number, amount, payment_method, processed_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """).bind(
        tx_id, timestamp, data['payer_name'], data.get('phone'), 
        data['amount'], data['method'], data['user_id']
    ).run()

    return jsonify({"status": "Success", "transaction_id": tx_id}), 201

# Worker Entrypoint
async def on_fetch(request, env):
    # This maps your D1 'DB' binding to the application
    import asgi_proxy_lib
    return await asgi_proxy_lib.fetch(app, request, env)
