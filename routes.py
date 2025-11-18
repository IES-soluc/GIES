import json
from flask import Blueprint, render_template, request, jsonify, send_file
from extensions import db
from models import Gleba
from utils import processar_geometria, gerar_csv_gleba, gerar_kml_gleba, gerar_shp_zip, processar_importacao_kml, processar_importacao_shp

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/api/glebas', methods=['GET'])
def get_glebas():
    glebas = Gleba.query.all()
    features = []
    for g in glebas:
        try:
            feature = json.loads(g.geojson)
            feature['properties'] = {
                'id': g.id,
                'nome': g.nome,
                'cor': g.cor or '#ffc107',
                'tipo': g.tipo,
                'area_ha': g.area_ha or 0.0,
                'comprimento_km': g.comprimento_km or 0.0
            }
            features.append(feature)
        except: continue
    return jsonify({"type": "FeatureCollection", "features": features})

@main.route('/api/glebas', methods=['POST'])
def add_gleba():
    data = request.json
    if not data or 'geojson' not in data:
        return jsonify({"error": "Dados inválidos"}), 400

    geom_data = data['geojson']['geometry']
    area, comp, tipo = processar_geometria(geom_data)
    
    nova_gleba = Gleba(
        nome=data.get('nome', 'Sem Nome'), 
        geojson=json.dumps(data['geojson']),
        cor=data.get('cor', '#ffc107'),
        tipo=tipo,
        area_ha=area,
        comprimento_km=comp
    )
    db.session.add(nova_gleba)
    db.session.commit()
    return jsonify({"message": "Salvo", "id": nova_gleba.id}), 201

@main.route('/api/glebas/<int:id>', methods=['PUT'])
def update_gleba(id):
    gleba = Gleba.query.get_or_404(id)
    data = request.json
    
    if 'nome' in data: gleba.nome = data['nome']
    if 'cor' in data: gleba.cor = data['cor']
    
    if 'geojson' in data and data['geojson'] is not None:
        gleba.geojson = json.dumps(data['geojson'])
        area, comp, tipo = processar_geometria(data['geojson']['geometry'])
        gleba.tipo = tipo
        gleba.area_ha = area
        gleba.comprimento_km = comp
    
    db.session.commit()
    return jsonify({"message": "Atualizada", "id": gleba.id})

@main.route('/api/glebas/<int:id>', methods=['DELETE'])
def delete_gleba(id):
    gleba = Gleba.query.get_or_404(id)
    db.session.delete(gleba)
    db.session.commit()
    return jsonify({"message": "Deletada"})

# --- Exportações ---

@main.route('/export/csv/<int:id>')
def export_csv(id):
    gleba = Gleba.query.get_or_404(id)
    output = gerar_csv_gleba(gleba)
    if not output: return "Erro na geometria", 400
    return send_file(output, mimetype="text/csv", as_attachment=True, download_name=f"{gleba.nome}_dados.csv")

@main.route('/export/kml/<int:id>')
def export_kml(id):
    gleba = Gleba.query.get_or_404(id)
    output = gerar_kml_gleba(gleba)
    return send_file(output, mimetype="application/vnd.google-earth.kml+xml", as_attachment=True, download_name=f"{gleba.nome}.kml")

@main.route('/export/shp/<int:id>')
def export_shp(id):
    gleba = Gleba.query.get_or_404(id)
    try:
        output = gerar_shp_zip(gleba)
        if not output: return "Tipo de geometria não suportado para SHP.", 400
        return send_file(output, mimetype="application/zip", as_attachment=True, download_name=f"{gleba.nome}_shp.zip")
    except Exception as e:
        return str(e), 500

# --- Importação Universal ---

@main.route('/import/universal', methods=['POST'])
def import_universal():
    if 'file' not in request.files: return jsonify({"error": "Sem arquivo"}), 400
    file = request.files['file']
    filename = file.filename.lower()
    
    dados_glebas = []
    try:
        if filename.endswith('.zip'):
            dados_glebas = processar_importacao_shp(file)
        else:
            dados_glebas = processar_importacao_kml(file)
            
        if not dados_glebas: return jsonify({"error": "Nenhuma geometria válida."}), 400
        
        count = 0
        for d in dados_glebas:
            nova = Gleba(
                nome=d['nome'], 
                geojson=d['geojson'], 
                area_ha=d['area_ha'], 
                comprimento_km=d['comprimento_km'], 
                tipo=d['tipo'], 
                cor='#3388ff'
            )
            db.session.add(nova)
            count += 1
        db.session.commit()
        return jsonify({"message": f"{count} itens importados."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500