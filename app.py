from flask import Flask
from extensions import db
from routes import main
from utils import limpar_glebas_antigas
from models import Gleba # Importa para passar para a função de limpeza

def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gies.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    app.register_blueprint(main)
    
    with app.app_context():
        db.create_all()
        
        # --- LIMPEZA AUTOMÁTICA AO INICIAR O SERVIDOR ---
        # Apaga registros com mais de 7 dias
        try:
            limpar_glebas_antigas(app, db, Gleba, dias=7)
        except Exception as e:
            print(f"Aviso: Erro ao tentar limpar banco: {e}")
            
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)