import json
import uuid
import os
from flask import Blueprint, render_template, request, jsonify, send_file, make_response, g
from extensions import db
from models import Gleba
from utils import processar_geometria, gerar_csv_gleba, gerar_kml_gleba, gerar_shp_zip, processar_importacao_kml, processar_importacao_shp

main = Blueprint('main', __name__)

# --- GESTÃO DE SESSÃO (COOKIE) ---
@main.before_request
def gerenciar_sessao():
    session_id = request.cookies.get('user_session')
    if not session_id:
        session_id = str(uuid.uuid4())
        g.set_new_cookie = True
    else:
        g.set_new_cookie = False
    g.user_session = session_id

@main.after_request
def setar_cookie(response):
    if g.get('set_new_cookie'):
        response.set_cookie('user_session', g.user_session, max_age=60*60*24*30)
    return response

# --- ROTAS ---

@main.route('/')
def index():
    return render_template('index.html')

# --- NOVO: Rota para servir a mensagem externa ---
@main.route('/api/message', methods=['GET'])
def get_external_message():
    message_path = os.path.join(main.root_path, 'static', 'data', 'message.json')
    
    if os.path.exists(message_path):
        try:
            with open(message_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return jsonify(data)
        except Exception as e:
            print(f"Erro ao ler message.json: {e}")
            return jsonify({"active": False}), 500
    
    return jsonify({"active": False}), 200

@main.route('/api/glebas', methods=['GET'])
def get_glebas():
    # FILTRA PELO ID DA SESSÃO
    glebas = Gleba.query.filter_by(session_id=g.user_session).all()
    
    features = []
    for r in glebas:
        try:
            feature = json.loads(r.geojson)
            feature['properties'] = {
                'id': r.id,
                'nome': r.nome,
                'cor': r.cor or '#FF7F00',
                'tipo': r.tipo,
                'area_ha': r.area_ha or 0.0,
                'comprimento_km': r.comprimento_km or 0.0
            }
            features.append(feature)
        except: continue
    return jsonify({"type": "FeatureCollection", "features": features})

@main.route('/api/glebas', methods=['POST'])
def add_gleba():
    data = request.json
    if not data or 'geojson' not in data: return jsonify({"error": "Dados inválidos"}), 400

    geom_data = data['geojson']['geometry']
    area, comp, tipo = processar_geometria(geom_data)
    
    nova_gleba = Gleba(
        nome=data.get('nome', 'Sem Nome'), 
        geojson=json.dumps(data['geojson']),
        cor=data.get('cor', '#FF7F00'),
        tipo=tipo,
        area_ha=area,
        comprimento_km=comp,
        session_id=g.user_session # SALVA SESSÃO
    )
    db.session.add(nova_gleba)
    db.session.commit()
    return jsonify({"message": "Salvo", "id": nova_gleba.id}), 201

@main.route('/api/glebas/<int:id>', methods=['PUT'])
def update_gleba(id):
    gleba = Gleba.query.filter_by(id=id, session_id=g.user_session).first_or_404()
    
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
    gleba = Gleba.query.filter_by(id=id, session_id=g.user_session).first_or_404()
    db.session.delete(gleba)
    db.session.commit()
    return jsonify({"message": "Deletada"})

# --- Rotas de Exportação e Importação (Permanecem no routes.py, chamando utils) ---

@main.route('/export/csv/<int:id>')
def export_csv(id):
    gleba = Gleba.query.filter_by(id=id, session_id=g.user_session).first_or_404()
    output = gerar_csv_gleba(gleba)
    if not output: return "Erro geometria", 400
    return send_file(output, mimetype="text/csv", as_attachment=True, download_name=f"{gleba.nome}.csv")

@main.route('/export/kml/<int:id>')
def export_kml(id):
    gleba = Gleba.query.filter_by(id=id, session_id=g.user_session).first_or_404()
    output = gerar_kml_gleba(gleba)
    return send_file(output, mimetype="application/vnd.google-earth.kml+xml", as_attachment=True, download_name=f"{gleba.nome}.kml")

@main.route('/export/shp/<int:id>')
def export_shp(id):
    gleba = Gleba.query.filter_by(id=id, session_id=g.user_session).first_or_404()
    try:
        output = gerar_shp_zip(gleba)
        if not output: return "Erro SHP", 400
        return send_file(output, mimetype="application/zip", as_attachment=True, download_name=f"{gleba.nome}_shp.zip")
    except Exception as e: return str(e), 500

@main.route('/import/universal', methods=['POST'])
def import_universal():
    if 'file' not in request.files: return jsonify({"error": "Sem arquivo"}), 400
    
    file = request.files['file']
    filename = file.filename.lower()
    
    try:
        dados = []
        if filename.endswith('.zip'): dados = processar_importacao_shp(file)
        else: dados = processar_importacao_kml(file)
            
        if not dados: return jsonify({"error": "Nada importado"}), 400
        
        count = 0
        for d in dados:
            nova = Gleba(
                nome=d['nome'], 
                geojson=d['geojson'], 
                area_ha=d['area_ha'], 
                comprimento_km=d['comprimento_km'], 
                tipo=d['tipo'], 
                cor='#3388ff',
                session_id=g.user_session # VINCULA AO USUARIO ATUAL
            )
            db.session.add(nova)
            count += 1
        db.session.commit()
        return jsonify({"message": f"{count} itens importados."})
    except Exception as e: return jsonify({"error": str(e)}), 500