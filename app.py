from flask import Flask
from extensions import db
from routes import main

def create_app():
    app = Flask(__name__)
    
    # Configurações
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gies.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializa DB
    db.init_app(app)
    
    # Registra Rotas
    app.register_blueprint(main)
    
    # Cria tabelas
    with app.app_context():
        db.create_all()
        
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)