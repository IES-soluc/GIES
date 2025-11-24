from flask import Flask, jsonify
from extensions import db
from routes import main
from utils import limpar_glebas_antigas
from models import Gleba

def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gies.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # --- NOVO: Limite de tamanho de arquivo (16 Megabytes) ---
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 
    
    # Define uma chave secreta para as sessões (obrigatório para segurança do cookie)
    app.config['SECRET_KEY'] = 'uma_chave_super_secreta_e_unica_para_o_gies' 

    db.init_app(app)
    app.register_blueprint(main)
    
    # --- Handler para erro 413 (Arquivo muito grande) ---
    @app.errorhandler(413)
    def file_too_large(e):
        return jsonify({"error": "Arquivo muito grande. O limite máximo de importação é 16MB."}), 413
    
    with app.app_context():
        db.create_all()
        
        # --- LIMPEZA AUTOMÁTICA AO INICIAR O SERVIDOR ---
        try:
            limpar_glebas_antigas(app, db, Gleba, dias=7)
        except Exception as e:
            print(f"Aviso: Erro ao tentar limpar banco: {e}")
            
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0')