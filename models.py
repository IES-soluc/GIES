from extensions import db
from datetime import datetime

class Gleba(db.Model):
    __tablename__ = 'glebas'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    geojson = db.Column(db.Text, nullable=False)
    
    # Metadados Geométricos
    tipo = db.Column(db.String(20), default='Polygon')
    area_ha = db.Column(db.Float, nullable=True)
    comprimento_km = db.Column(db.Float, nullable=True)
    cor = db.Column(db.String(7), default='#ffc107')
    
    # --- NOVOS CAMPOS PARA SESSÃO ---
    session_id = db.Column(db.String(36), nullable=False, index=True) # ID do Cookie
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # Data de criação

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'geojson': self.geojson,
            'tipo': self.tipo,
            'area_ha': self.area_ha,
            'comprimento_km': self.comprimento_km,
            'cor': self.cor,
            'created_at': self.created_at.isoformat()
        }