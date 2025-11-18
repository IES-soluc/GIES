CHANGELOG - GIES (Geospatial Information Editing System)

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

## v1.1.0 - [18/11/2025] - Versão Conteinerizada

### Adicionado
* **Suporte a Containerização:** Criação de `Dockerfile`, `docker-compose.yml` e `.dockerignore` para padronizar o ambiente de execução via Docker.
* **Servidor de Produção:** Implementação de Gunicorn para servir a aplicação Flask em ambiente conteinerizado.
* **Importação/Exportação SHP (Shapefile):** Adicionado suporte para importação e exportação de geometrias no formato SHP (compactado em ZIP) utilizando a biblioteca `pyshp`.
* **Importação Universal:** A rota `/import/universal` agora detecta automaticamente se o arquivo é KML ou ZIP (SHP).

### Melhorias
* Refatoração do parser KML para ser **agnóstico a namespaces**, corrigindo falhas na importação de KMLs gerados por diferentes softwares.
* Melhorias na performance e usabilidade da UI.

## v1.0.1 - [17/11/2025] - Versão Preparada para Multi-Usuários (Sessões)

### Alterado
* **Arquitetura de Dados:** Implementada segregação de dados por `session_id` (Cookie/UUID) para evitar que usuários vejam/editem os dados uns dos outros.
* **Limpeza Automática:** Adicionada rotina para apagar automaticamente as glebas com mais de 7 dias de idade, garantindo a performance do banco de dados (SQLite) e gerenciamento de recursos.

### Melhorias
* **Edição de Propriedades:** Adicionada funcionalidade para editar o nome e a cor de geometrias já existentes via modal na lista lateral (sem a necessidade de editar a geometria no mapa).

## v1.0.0 - [15/11/2025] - Versão Base Funcional

### Funcionalidades Iniciais
* **CRUD Base:** Implementação inicial das rotas POST, GET, PUT, DELETE para Polígonos.
* **Suporte a Geometrias:** Adicionado suporte para desenhar e salvar Polígonos, Linhas e Pontos.
* **Cálculo Geoespacial:** Implementação de `Shapely` e `Pyproj` para calcular Área (ha) e Comprimento (km) com precisão.
* **Exportação Inicial:** Criação das rotas de exportação para KML e CSV (com coordenadas DMS/UTM).
* **UI/UX:** Configuração inicial do mapa Leaflet, busca de localidade e estilo de mapa híbrido.