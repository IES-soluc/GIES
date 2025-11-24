document.addEventListener('DOMContentLoaded', function() {
    
    let layerAtual = null;
    const modalGleba = new bootstrap.Modal(document.getElementById('modalGleba'));
    
    // --- 1. Mapa ---
    var map = L.map('map').setView([-15.7942, -47.8822], 4);
    
    var osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: 'OSM', maxZoom: 19 });
    var googleHybrid = L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', { maxZoom: 20, attribution: 'Google' });
    
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
    
    // Grupo exclusivo para números (Labels)
    var vertexLabelsGroup = new L.LayerGroup().addTo(map);

    var drawControl = new L.Control.Draw({
        draw: {
            polygon: { allowIntersection: false, showArea: true, shapeOptions: { color: '#999', dashArray: '5, 5' } },
            polyline: { shapeOptions: { color: '#999', dashArray: '5, 5' } },
            marker: true, circle: false, circlemarker: false, rectangle: false
        },
        edit: { featureGroup: drawnItems, remove: false }
    });
    map.addControl(drawControl);

    // --- 4. Lógica de Numeração (CORRIGIDA) ---

    function updateVertexLabels() {
        vertexLabelsGroup.clearLayers(); // Limpa para redesenhar
        
        drawnItems.eachLayer(function(layer) {
            // Verifica se a camada está em modo de edição
            if (layer.editing && layer.editing.enabled()) {
                let latlngs;

                // Verifica tipo de geometria para pegar coordenadas corretamente
                // Polígono: Array de Arrays (Anéis). Pegamos o primeiro anel [0].
                // Linha: Array de LatLngs direto.
                if (layer instanceof L.Polygon) {
                    latlngs = layer.getLatLngs()[0];
                } else if (layer instanceof L.Polyline) {
                    latlngs = layer.getLatLngs();
                }

                // Se encontrou coordenadas válidas, desenha os números
                if (latlngs && Array.isArray(latlngs)) {
                    latlngs.forEach((latlng, index) => {
                        // Pega o ponto lat/lng correto (Leaflet pode aninhar objetos)
                        // Garante que é um objeto latlng válido
                        if (!latlng.lat) return; 

                        L.marker(latlng, {
                            icon: L.divIcon({
                                className: 'vertex-label', 
                                html: (index + 1).toString(),
                                
                                // TAMANHO FIXO É ESSENCIAL PARA NÃO AGLOMERAR
                                iconSize: [18, 18], 
                                
                                // Desloca o ícone (x, y) em pixels relativo ao vértice
                                // Negativo X = Esquerda, Positivo X = Direita
                                // Negativo Y = Cima, Positivo Y = Baixo
                                iconAnchor: [9, 9] 
                            }),
                            interactive: false, // Mouse ignora o número
                            zIndexOffset: 1000
                        }).addTo(vertexLabelsGroup);
                    });
                }
            }
        });
    }

    // --- Listeners Globais de Edição ---
    
    // Disparado ao clicar no botão "Edit Layers" e selecionar a gleba
    map.on('draw:editstart', function() {
        // Pequeno delay para garantir que o Leaflet calculou as posições
        setTimeout(updateVertexLabels, 10);
    });

    // Disparado ao parar a edição (Salvar/Cancelar)
    map.on('draw:editstop', function() {
        vertexLabelsGroup.clearLayers();
    });

    // Disparado a cada pixel que arrasta o vértice
    map.on('draw:editmove', function() {
        updateVertexLabels();
    });
    
    // Disparado ao adicionar/remover vértice da linha
    map.on('draw:editvertex', function() {
        updateVertexLabels();
    });


    // --- 5. Funções Auxiliares ---

    function getDescricaoMedida(props) {
        if (props.tipo === 'Polygon') return (props.area_ha || 0).toFixed(4).replace('.', ',') + ' ha';
        if (props.tipo === 'LineString') return (props.comprimento_km || 0).toFixed(3).replace('.', ',') + ' km';
        return 'Ponto';
    }

    function getIconeTipo(tipo) {
        if (tipo === 'Polygon') return '<i class="fa-solid fa-draw-polygon"></i>';
        if (tipo === 'LineString') return '<i class="fa-solid fa-route"></i>';
        return '<i class="fa-solid fa-location-dot"></i>';
    }
    
    function loadExternalWarning() {
        fetch('/api/message')
            .then(res => res.json())
            .then(data => {
                if (data.active && data.content) {
                    const modalElement = document.getElementById('warningModal');
                    const modal = new bootstrap.Modal(modalElement);
                    document.getElementById('warningModalTitle').innerText = data.title || "Aviso";
                    document.getElementById('warningModalContent').innerHTML = data.content;
                    modal.show();
                }
            }).catch(err => console.log(err));
    }

    function loadGlebas() {
        fetch('/api/glebas')
            .then(res => res.json())
            .then(data => {
                drawnItems.clearLayers();
                const listDiv = document.getElementById('gleba-list');
                listDiv.innerHTML = '';

                if(data.features.length === 0) listDiv.innerHTML = '<div class="text-center mt-4 text-muted">Nada cadastrado.</div>';

                L.geoJSON(data, {
                    pointToLayer: function (feature, latlng) {
                        const cor = feature.properties.cor || '#FF7F00';
                        const customIcon = L.divIcon({
                            className: 'custom-pin-icon',
                            html: `<div style="background-color:${cor};width:30px;height:30px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);border:2px solid white;box-shadow:2px 2px 5px rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;"><i class="fa-solid fa-location-dot" style="color:white;font-size:14px;transform:rotate(45deg);"></i></div>`,
                            iconSize: [30, 42], iconAnchor: [15, 42], popupAnchor: [0, -40]
                        });
                        return L.marker(latlng, { icon: customIcon });
                    },
                    style: function(feature) {
                        return {
                            color: feature.properties.cor,
                            fillColor: feature.properties.cor,
                            weight: feature.properties.tipo === 'LineString' ? 5 : 2,
                            opacity: 1, fillOpacity: 0.4
                        };
                    },
                    onEachFeature: function (feature, layer) {
                        const props = feature.properties;
                        layer.featureId = props.id;
                        layer.featureNome = props.nome;
                        layer.featureCor = props.cor;

                        drawnItems.addLayer(layer);
                        
                        layer.bindPopup(`<div class="text-center"><strong style="color:${props.cor}">${props.nome}</strong><br><span class="badge bg-secondary">${getDescricaoMedida(props)}</span></div>`);
                        
                        const item = document.createElement('div');
                        item.className = 'gleba-item';
                        item.style.borderLeft = `5px solid ${props.cor}`;
                        item.innerHTML = `
                            <div class="d-flex justify-content-between align-items-start">
                                <div style="overflow:hidden;"><strong class="d-block text-truncate">${props.nome}</strong><small class="text-muted">${getIconeTipo(props.tipo)} ${getDescricaoMedida(props)}</small></div>
                                <div class="btn-group btn-group-sm">
                                    <button onclick="editarPropriedades(${props.id}, '${props.nome}', '${props.cor}')" class="btn btn-outline-secondary"><i class="fa-solid fa-pen"></i></button>
                                    <a href="/export/csv/${props.id}" class="btn btn-outline-success"><i class="fa-solid fa-file-csv"></i></a>
                                    <a href="/export/kml/${props.id}" class="btn btn-outline-primary"><i class="fa-solid fa-globe"></i></a>
                                    <a href="/export/shp/${props.id}" class="btn btn-outline-warning"><i class="fa-solid fa-layer-group"></i></a>
                                </div>
                                <button onclick="deleteGleba(${props.id}, event)" class="btn btn-outline-danger btn-sm ms-1"><i class="fa-solid fa-trash"></i></button>
                            </div>`;
                        
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
            });
    }

    // --- 6. Eventos ---
    
    map.on(L.Draw.Event.CREATED, function (e) {
        layerAtual = e.layer;
        drawnItems.addLayer(layerAtual);
        document.getElementById('modalTitulo').innerText = "Nova Gleba";
        document.getElementById('inputId').value = "";
        document.getElementById('inputNome').value = "";
        document.getElementById('inputCor').value = "#FF7F00";
        modalGleba.show();
        
        // Força atualização de labels se criar novo
        setTimeout(updateVertexLabels, 100);
    });

    window.editarPropriedades = function(id, nome, cor) {
        document.getElementById('modalTitulo').innerText = "Editar Gleba";
        document.getElementById('inputId').value = id;
        document.getElementById('inputNome').value = nome;
        document.getElementById('inputCor').value = cor;
        modalGleba.show();
    }

    document.getElementById('formGleba').addEventListener('submit', function(e){
        e.preventDefault();
        const id = document.getElementById('inputId').value;
        const nome = document.getElementById('inputNome').value;
        const cor = document.getElementById('inputCor').value;
        
        if (id) {
            fetch(`/api/glebas/${id}`, {
                method: 'PUT', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ nome: nome, cor: cor })
            }).then(() => { modalGleba.hide(); loadGlebas(); });
        } else if (layerAtual) {
            const geojson = layerAtual.toGeoJSON();
            fetch('/api/glebas', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ nome: nome, cor: cor, geojson: geojson })
            }).then(() => { modalGleba.hide(); layerAtual = null; loadGlebas(); });
        }
    });

    window.cancelarCriacao = function() {
        if(layerAtual) { drawnItems.removeLayer(layerAtual); layerAtual = null; }
        modalGleba.hide();
        vertexLabelsGroup.clearLayers();
    }

    map.on(L.Draw.Event.EDITED, function (e) {
        vertexLabelsGroup.clearLayers();
        let updates = [];
        e.layers.eachLayer(layer => {
            if (layer.featureId) {
                updates.push(fetch(`/api/glebas/${layer.featureId}`, {
                    method: 'PUT', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ geojson: layer.toGeoJSON(), nome: layer.featureNome, cor: layer.featureCor })
                }));
            }
        });
        Promise.all(updates).then(() => loadGlebas());
    });

    window.deleteGleba = function(id, evt) {
        evt.stopPropagation();
        if(confirm('Excluir?')) fetch(`/api/glebas/${id}`, {method:'DELETE'}).then(loadGlebas);
    }

    document.getElementById('formImport').addEventListener('submit', function(e){
        e.preventDefault();
        const btn = this.querySelector('button[type="submit"]');
        const old = btn.innerText; btn.innerText = '...';
        fetch('/import/universal', { method: 'POST', body: new FormData(this) })
        .then(res => res.json())
        .then(data => { alert(data.message || data.error); loadGlebas(); bootstrap.Modal.getInstance(document.getElementById('importModal')).hide(); })
        .finally(() => { btn.innerText = old; this.reset(); });
    });

    loadGlebas();
    loadExternalWarning();
});