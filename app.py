import uuid
from datetime import datetime
from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agri_corp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELS ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    role = db.Column(db.String(20)) # e.g., 'Admin', 'Field Agent'

class Client(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())[:8]) # Short ID for easy access
    name = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(50))
    onboarded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    details = db.Column(db.Text)
    is_editable = db.Column(db.Boolean, default=False) # Controlled by permission system

class FinancialLedger(db.Model):
    # This table is "Append-Only" - No Update or Delete routes will be created
    tx_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    payer_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    bank_account = db.Column(db.String(50), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(30)) # Mobile Money, Bank, etc.
    processed_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class EditRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.String(36), db.ForeignKey('client.id'))
    requested_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='Pending') # Pending, Approved, Denied

# --- ROUTES ---

@app.route('/api/client/<client_id>', methods=['GET'])
def get_client(client_id):
    client = Client.query.get_or_404(client_id)
    return jsonify({
        "id": client.id,
        "name": client.name,
        "region": client.region,
        "onboarder_id": client.onboarded_by,
        "details": client.details
    })

@app.route('/api/transaction', methods=['POST'])
def create_transaction():
    data = request.json
    # Generate an immutable record
    new_tx = FinancialLedger(
        payer_name=data['payer_name'],
        phone_number=data.get('phone'),
        bank_account=data.get('bank_acc'),
        amount=data['amount'],
        payment_method=data['method'],
        processed_by=data['user_id']
    )
    db.session.add(new_tx)
    db.session.commit()
    return jsonify({"status": "Success", "transaction_id": new_tx.tx_id}), 201

@app.route('/api/client/<client_id>/request-edit', methods=['POST'])
def request_edit(client_id):
    user_id = request.json.get('user_id')
    new_request = EditRequest(client_id=client_id, requested_by=user_id)
    db.session.add(new_request)
    db.session.commit()
    return jsonify({"message": "Edit request submitted to Admin."})

# Worker Entrypoint
async def on_fetch(request, env):
    from workers import asgi
    return await asgi.fetch(app, request, env)
