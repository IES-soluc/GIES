document.addEventListener('DOMContentLoaded', function() {
    
    let layerAtual = null;
    const modalGleba = new bootstrap.Modal(document.getElementById('modalGleba'));
    
    // --- 1. Inicialização do Mapa ---
    var map = L.map('map').setView([-15.7942, -47.8822], 4);
    
    var osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { 
        attribution: 'OSM', maxZoom: 19 
    });
    
    var googleHybrid = L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', { 
        maxZoom: 20, attribution: 'Google Maps' 
    });
    
    googleHybrid.addTo(map);
    L.control.layers({ "Híbrido": googleHybrid, "Ruas": osm }).addTo(map);

    // --- 2. Busca ---
    if (window.GeoSearch) {
        const provider = new GeoSearch.OpenStreetMapProvider();
        map.addControl(new GeoSearch.GeoSearchControl({
            provider: provider, style: 'bar', showMarker: true, autoClose: true, searchLabel: 'Buscar local...'
        }));
    }

    // --- 3. Ferramentas de Desenho ---
    var drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    var drawControl = new L.Control.Draw({
        draw: {
            polygon: { 
                allowIntersection: false, 
                showArea: true, 
                shapeOptions: { color: '#999', dashArray: '5, 5' } 
            },
            polyline: { 
                shapeOptions: { color: '#999', dashArray: '5, 5' } 
            },
            marker: true, // Habilita pontos
            circle: false, 
            circlemarker: false, 
            rectangle: false
        },
        edit: { featureGroup: drawnItems, remove: false }
    });
    map.addControl(drawControl);

    // --- 4. Funções de Exibição ---

    function getDescricaoMedida(props) {
        if (props.tipo === 'Polygon') return (props.area_ha || 0).toFixed(4).replace('.', ',') + ' ha';
        if (props.tipo === 'LineString') return (props.comprimento_km || 0).toFixed(3).replace('.', ',') + ' km';
        return 'Ponto de Interesse';
    }

    function getIconeTipo(tipo) {
        if (tipo === 'Polygon') return '<i class="fa-solid fa-draw-polygon"></i>';
        if (tipo === 'LineString') return '<i class="fa-solid fa-route"></i>';
        return '<i class="fa-solid fa-location-dot"></i>';
    }

    function loadGlebas() {
        fetch('/api/glebas')
            .then(res => res.json())
            .then(data => {
                drawnItems.clearLayers();
                const listDiv = document.getElementById('gleba-list');
                listDiv.innerHTML = '';

                if(data.features.length === 0) {
                    listDiv.innerHTML = '<div class="text-center mt-4 text-muted">Nenhum item cadastrado.<br>Desenhe no mapa.</div>';
                }

                L.geoJSON(data, {
                    
                    // --- CUSTOMIZAÇÃO DO PONTO (PIN) ---
                    pointToLayer: function (feature, latlng) {
                        const cor = feature.properties.cor || '#ff7700';
                        
                        // Cria um ícone HTML personalizado (DivIcon)
                        const customIcon = L.divIcon({
                            className: 'custom-pin-icon',
                            html: `
                                <div style="
                                    background-color: ${cor};
                                    width: 30px;
                                    height: 30px;
                                    border-radius: 50% 50% 50% 0;
                                    transform: rotate(-45deg);
                                    border: 2px solid white;
                                    box-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                ">
                                    <i class="fa-solid fa-circle" style="
                                        color: white; 
                                        font-size: 10px; 
                                        transform: rotate(45deg);
                                    "></i>
                                </div>
                            `,
                            iconSize: [30, 42], // Tamanho do ícone
                            iconAnchor: [15, 42], // Onde a ponta do ícone toca o mapa
                            popupAnchor: [0, -40] // Onde o popup abre
                        });

                        return L.marker(latlng, { icon: customIcon });
                    },

                    // --- ESTILO DE LINHAS E POLÍGONOS ---
                    style: function(feature) {
                        return {
                            color: feature.properties.cor,
                            fillColor: feature.properties.cor,
                            weight: feature.properties.tipo === 'LineString' ? 5 : 2,
                            opacity: 1,
                            fillOpacity: 0.4
                        };
                    },

                    onEachFeature: function (feature, layer) {
                        const props = feature.properties;
                        
                        // Salva metadados no layer para edição
                        layer.featureId = props.id;
                        layer.featureNome = props.nome;
                        layer.featureCor = props.cor;

                        drawnItems.addLayer(layer);
                        
                        // Popup
                        layer.bindPopup(`
                            <div class="text-center">
                                <strong style="color:${props.cor}">${props.nome}</strong><br>
                                <span class="badge bg-secondary">${getDescricaoMedida(props)}</span>
                            </div>
                        `);
                        
                        // Item da Lista
                        const item = document.createElement('div');
                        item.className = 'gleba-item';
                        item.style.borderLeft = `5px solid ${props.cor}`;
                        
                        item.innerHTML = `
                            <div class="d-flex justify-content-between align-items-start">
                                <div style="overflow:hidden;">
                                    <strong class="d-block text-truncate" title="${props.nome}">${props.nome}</strong>
                                    <div class="text-muted small mb-1">
                                        ${getIconeTipo(props.tipo)} ${getDescricaoMedida(props)}
                                    </div>
                                </div>
                                <div class="d-flex flex-column gap-1">
                                    <div class="btn-group btn-group-sm">
                                        <button onclick="editarPropriedades(${props.id}, '${props.nome}', '${props.cor}')" class="btn btn-outline-secondary" title="Editar"><i class="fa-solid fa-pen"></i></button>
                                        <a href="/export/csv/${props.id}" class="btn btn-outline-success" title="CSV"><i class="fa-solid fa-file-csv"></i></a>
                                        <a href="/export/kml/${props.id}" class="btn btn-outline-primary" title="KML"><i class="fa-solid fa-globe"></i></a>
                                        <a href="/export/shp/${props.id}" class="btn btn-outline-warning" title="SHP (Zip)"><i class="fa-solid fa-layer-group"></i></a>
                                    </div>
                                    <button onclick="deleteGleba(${props.id}, event)" class="btn btn-outline-danger btn-sm w-100"><i class="fa-solid fa-trash"></i></button>
                                </div>
                            </div>
                        `;
                        
                        // Zoom ao clicar
                        item.addEventListener('click', (e) => {
                            if(!e.target.closest('.btn') && !e.target.closest('a')) {
                                if(layer.getBounds) map.fitBounds(layer.getBounds());
                                else map.setView(layer.getLatLng(), 16);
                                layer.openPopup();
                            }
                        });

                        listDiv.appendChild(item);
                    }
                });
            })
            .catch(err => console.error("Erro:", err));
    }

    // --- 5. Eventos (Criar, Editar, Deletar) ---
    
    // Criar
    map.on(L.Draw.Event.CREATED, function (e) {
        layerAtual = e.layer;
        drawnItems.addLayer(layerAtual);
        
        // Preenche modal criação
        document.getElementById('modalTitulo').innerText = "Nova Gleba";
        document.getElementById('inputId').value = "";
        document.getElementById('inputNome').value = "";
        document.getElementById('inputCor').value = "#ff7700";
        modalGleba.show();
    });

    // Função Editar Propriedades (Chamada pelo botão da lista)
    window.editarPropriedades = function(id, nome, cor) {
        document.getElementById('modalTitulo').innerText = "Editar Gleba";
        document.getElementById('inputId').value = id;
        document.getElementById('inputNome').value = nome;
        document.getElementById('inputCor').value = cor;
        modalGleba.show();
    }

    // Submit do Modal
    document.getElementById('formGleba').addEventListener('submit', function(e){
        e.preventDefault();
        const id = document.getElementById('inputId').value;
        const nome = document.getElementById('inputNome').value;
        const cor = document.getElementById('inputCor').value;
        
        // Edição
        if (id) {
            fetch(`/api/glebas/${id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ nome: nome, cor: cor })
            })
            .then(res => res.json())
            .then(() => { modalGleba.hide(); loadGlebas(); });
        }
        // Criação
        else if (layerAtual) {
            const geojson = layerAtual.toGeoJSON();
            fetch('/api/glebas', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ nome: nome, cor: cor, geojson: geojson })
            })
            .then(res => res.json())
            .then(() => { modalGleba.hide(); layerAtual = null; loadGlebas(); });
        }
    });

    // Cancelar
    window.cancelarCriacao = function() {
        if(layerAtual) {
            drawnItems.removeLayer(layerAtual);
            layerAtual = null;
        }
        modalGleba.hide();
    }

    // Evento Editar Geometria (Arrastar vértices)
    map.on(L.Draw.Event.EDITED, function (e) {
        let updates = [];
        e.layers.eachLayer(layer => {
            if (layer.featureId) {
                const p = fetch(`/api/glebas/${layer.featureId}`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ 
                        geojson: layer.toGeoJSON(), 
                        nome: layer.featureNome, 
                        cor: layer.featureCor 
                    })
                });
                updates.push(p);
            }
        });
        Promise.all(updates).then(() => loadGlebas());
    });

    // Deletar
    window.deleteGleba = function(id, evt) {
        if(evt) evt.stopPropagation();
        if(confirm('Excluir permanentemente?')) {
            fetch(`/api/glebas/${id}`, { method: 'DELETE' }).then(loadGlebas);
        }
    }

    // Importar
    document.getElementById('formImport').addEventListener('submit', function(e){
        e.preventDefault();
        const btn = this.querySelector('button[type="submit"]');
        const oldTxt = btn.innerText;
        btn.innerText = 'Processando...';
        
        fetch('/import/universal', { method: 'POST', body: new FormData(this) })
        .then(res => res.json())
        .then(data => {
            alert(data.message || data.error);
            loadGlebas();
            bootstrap.Modal.getInstance(document.getElementById('importModal')).hide();
        })
        .finally(() => { btn.innerText = oldTxt; this.reset(); });
    });

    loadGlebas();
});