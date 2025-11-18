from extensions import db

class Gleba(db.Model):
    __tablename__ = 'glebas'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    geojson = db.Column(db.Text, nullable=False)
    
    # Metadados da Geometria
    tipo = db.Column(db.String(20), default='Polygon') # Pode ser: Polygon, LineString, Point
    area_ha = db.Column(db.Float, nullable=True)       # Usado para Polígonos
    comprimento_km = db.Column(db.Float, nullable=True)# Usado para Linhas
    
    cor = db.Column(db.String(7), default='#ffc107')   # Cor Hexadecimal

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'geojson': self.geojson,
            'tipo': self.tipo,
            'area_ha': self.area_ha,
            'comprimento_km': self.comprimento_km,
            'cor': self.cor
        }