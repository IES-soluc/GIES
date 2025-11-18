import json
import csv
import io
import os
import tempfile
import zipfile
import xml.etree.ElementTree as ET
import shapefile
from shapely.geometry import shape
from shapely.ops import transform
import pyproj
from datetime import datetime, timedelta

# --- Funções Auxiliares ---

def decimal_para_dms(valor, eixo):
    is_positive = valor >= 0
    valor_abs = abs(valor)
    graus = int(valor_abs)
    minutos_full = (valor_abs - graus) * 60
    minutos = int(minutos_full)
    segundos = (minutos_full - minutos) * 60
    direcao = ("N" if is_positive else "S") if eixo == 'lat' else ("E" if is_positive else "W")
    return f"{graus}° {minutos}' {segundos:.4f}\" {direcao}"

def obter_projecao_utm(lon, lat):
    zona_numero = int((lon + 180) / 6) + 1
    base_epsg = 32700 if lat < 0 else 32600
    epsg_final = base_epsg + zona_numero
    crs_wgs84 = pyproj.CRS('EPSG:4326')
    crs_utm = pyproj.CRS(f'EPSG:{epsg_final}')
    return pyproj.Transformer.from_crs(crs_wgs84, crs_utm, always_xy=True), zona_numero, ("S" if lat < 0 else "N")

def processar_geometria(geojson_dict):
    try:
        tipo = geojson_dict['type']
        geom = shape(geojson_dict)
        wgs84 = pyproj.CRS('EPSG:4326')
        albers = pyproj.CRS('EPSG:6933')
        project = pyproj.Transformer.from_crs(wgs84, albers, always_xy=True).transform
        projected_geom = transform(project, geom)
        
        area = 0.0
        comprimento = 0.0
        
        if tipo == 'Polygon':
            area = projected_geom.area / 10000.0
            comprimento = projected_geom.length / 1000.0
        elif tipo == 'LineString':
            comprimento = projected_geom.length / 1000.0
            
        return round(area, 4), round(comprimento, 4), tipo
    except Exception as e:
        return 0.0, 0.0, 'Unknown'

# --- Exportação ---

def gerar_csv_gleba(gleba):
    data = json.loads(gleba.geojson)
    tipo = data['geometry']['type']
    coords_raw = data['geometry']['coordinates']
    
    lista_coords = []
    if tipo == 'Point': lista_coords = [coords_raw]
    elif tipo == 'LineString': lista_coords = coords_raw
    elif tipo == 'Polygon': lista_coords = coords_raw[0]
    else: return None
    
    si = io.StringIO()
    cw = csv.writer(si, delimiter=';')
    cw.writerow(['Ponto', 'Latitude', 'Longitude', 'Lat DMS', 'Lon DMS', 'UTM X', 'UTM Y', 'Zona'])
    
    for i, p in enumerate(lista_coords, start=1):
        lon, lat = p[0], p[1]
        lat_dms = decimal_para_dms(lat, 'lat')
        lon_dms = decimal_para_dms(lon, 'lon')
        transformer, zona, hemi = obter_projecao_utm(lon, lat)
        e, n = transformer.transform(lon, lat)
        cw.writerow([i, f"{lat:.8f}".replace('.',','), f"{lon:.8f}".replace('.',','), lat_dms, lon_dms, f"{e:.3f}".replace('.',','), f"{n:.3f}".replace('.',','), f"{zona}{hemi}"])
        
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8-sig'))
    output.seek(0)
    return output

def gerar_kml_gleba(gleba):
    data = json.loads(gleba.geojson)
    tipo = data['geometry']['type']
    coords = data['geometry']['coordinates']
    def fmt(c): return f"{c[0]},{c[1]},0"
    
    kml_body = ""
    if tipo == 'Point': kml_body = f"<Point><coordinates>{fmt(coords)}</coordinates></Point>"
    elif tipo == 'LineString': kml_body = f"<LineString><coordinates>{' '.join([fmt(c) for c in coords])}</coordinates></LineString>"
    elif tipo == 'Polygon': kml_body = f"<Polygon><outerBoundaryIs><LinearRing><coordinates>{' '.join([fmt(c) for c in coords[0]])}</coordinates></LinearRing></outerBoundaryIs></Polygon>"

    kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Placemark>
    <name>{gleba.nome}</name>
    <Style><LineStyle><color>ff0000ff</color><width>3</width></LineStyle><PolyStyle><color>7f00ff00</color></PolyStyle></Style>
    {kml_body}
  </Placemark>
</kml>"""
    output = io.BytesIO()
    output.write(kml_content.encode('utf-8'))
    output.seek(0)
    return output

def gerar_shp_zip(gleba):
    geojson = json.loads(gleba.geojson)
    geom_type = geojson['geometry']['type']
    shp_type = None
    if geom_type == 'Point': shp_type = shapefile.POINT
    elif geom_type == 'LineString': shp_type = shapefile.POLYLINE
    elif geom_type == 'Polygon': shp_type = shapefile.POLYGON
    else: return None

    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = os.path.join(temp_dir, "export")
        w = shapefile.Writer(base_path, shp_type)
        w.field('NOME', 'C', size=100)
        w.field('AREA_HA', 'N', decimal=4)
        w.field('COMP_KM', 'N', decimal=4)
        w.record(gleba.nome, gleba.area_ha or 0, gleba.comprimento_km or 0)
        w.shape(geojson['geometry'])
        w.close()
        
        wgs84_wkt = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]'
        with open(base_path + ".prj", "w") as prj: prj.write(wgs84_wkt)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for ext in [".shp", ".shx", ".dbf", ".prj"]:
                if os.path.exists(base_path + ext): zip_file.write(base_path + ext, f"{gleba.nome}{ext}")
        zip_buffer.seek(0)
        return zip_buffer

# --- Importação ---

def parse_kml_coordinates(coord_text):
    if not coord_text: return []
    text = coord_text.strip().replace('\n', ' ').replace('\t', ' ')
    parts = text.split(' ')
    coords = []
    for p in parts:
        if not p.strip(): continue
        xyz = p.split(',')
        if len(xyz) >= 2:
            try: coords.append([float(xyz[0]), float(xyz[1])])
            except: continue
    return coords

def get_tag_name(element):
    if '}' in element.tag: return element.tag.split('}', 1)[1]
    return element.tag

def processar_importacao_kml(file_obj):
    try:
        tree = ET.parse(file_obj)
        root = tree.getroot()
    except: return []

    glebas = []
    for elem in root.iter():
        if get_tag_name(elem) == 'Placemark':
            name = "Importada KML"
            geojson = None
            for child in elem.iter():
                tag = get_tag_name(child)
                if tag == 'name': name = child.text
                elif tag == 'Polygon':
                    for sub in child.iter():
                        if get_tag_name(sub) == 'coordinates':
                            coords = parse_kml_coordinates(sub.text)
                            if len(coords) > 2: geojson = {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [coords]}}
                elif tag == 'LineString' and not geojson:
                    for sub in child.iter():
                        if get_tag_name(sub) == 'coordinates':
                            coords = parse_kml_coordinates(sub.text)
                            if len(coords) > 1: geojson = {"type": "Feature", "geometry": {"type": "LineString", "coordinates": coords}}
                elif tag == 'Point' and not geojson:
                    for sub in child.iter():
                        if get_tag_name(sub) == 'coordinates':
                            coords = parse_kml_coordinates(sub.text)
                            if len(coords) > 0: geojson = {"type": "Feature", "geometry": {"type": "Point", "coordinates": coords[0]}}
            if geojson:
                geojson['properties'] = {}
                area, comp, tipo = processar_geometria(geojson['geometry'])
                glebas.append({"nome": name, "geojson": json.dumps(geojson), "area_ha": area, "comprimento_km": comp, "tipo": tipo})
    return glebas

def processar_importacao_shp(file_obj):
    glebas = []
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            zip_path = os.path.join(temp_dir, "upload.zip")
            file_obj.save(zip_path)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref: zip_ref.extractall(temp_dir)
            shp_file = None
            for root, dirs, files in os.walk(temp_dir):
                for f in files:
                    if f.lower().endswith('.shp'):
                        shp_file = os.path.join(root, f)
                        break
                if shp_file: break
            if not shp_file: return []
            reader = shapefile.Reader(shp_file)
            for shape_record in reader.shapeRecords():
                try:
                    geom_interface = shape_record.shape.__geo_interface__
                    nome = "Importada SHP"
                    for record_item in shape_record.record:
                        if isinstance(record_item, str):
                            nome = record_item
                            break
                    geojson_struct = {"type": "Feature", "properties": {}, "geometry": geom_interface}
                    area, comp, tipo = processar_geometria(geojson_struct['geometry'])
                    glebas.append({"nome": nome, "geojson": json.dumps(geojson_struct), "area_ha": area, "comprimento_km": comp, "tipo": tipo})
                except: continue
        except: return []
    return glebas

# --- LIMPEZA DO BANCO (NOVA) ---
def limpar_glebas_antigas(app, db, Gleba_Model, dias=7):
    """ Apaga registros criados há mais de X dias """
    with app.app_context():
        limite = datetime.utcnow() - timedelta(days=dias)
        # Deleta onde created_at < limite
        num_deletados = Gleba_Model.query.filter(Gleba_Model.created_at < limite).delete()
        db.session.commit()
        if num_deletados > 0:
            print(f"LIMPEZA: {num_deletados} glebas antigas removidas.")