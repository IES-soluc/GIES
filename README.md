# 🌍 GIES (Geospatial Information Editing System)

O GIES é uma aplicação web moderna e responsiva construída com **Python Flask** e **Leaflet.js** para gestão e manipulação de geometrias geoespaciais (glebas, linhas e pontos). O sistema foi arquitetado para ser leve, rápido e preparado para um ambiente de teste multi-usuário (segregado por sessões/cookies).

---

## 💻 Funcionalidades Principais

* **Mapa Interativo Híbrido:** Utiliza Google Hybrid (Satélite com rótulos) para visualização moderna.
* **CRUD Geoespacial:** Permite **Criar, Ler, Atualizar e Excluir** (CRUD) Polígonos (Glebas), Linhas e Pontos diretamente no mapa.
* **Edição Visual:** Permite mover e editar os vértices das geometrias com **marcadores de vértice customizados** (círculos) para melhor usabilidade.
* **Customização de Estilo:** Permite que o usuário **escolha a cor** de cada geometria criada ou editada.
* **Cálculo Automático:** Exibe a **área em hectares (ha)** para Polígonos e o **comprimento em quilômetros (km)** para Linhas, utilizando projeções precisas (`Shapely`/`Pyproj`).
* **Segregação por Sessão:** Dados são visíveis apenas para o usuário atual (baseado em cookie/sessão) e são **excluídos automaticamente após 7 dias** para limpeza do banco de dados (SQLite).

---

## 📥 Importação e Exportação de Dados

O GIES suporta os principais formatos de intercâmbio de dados GIS.

| Formato | Tipo | Detalhes da Exportação |
| :--- | :--- | :--- |
| **Shapefile (.zip)** | Exportar/Importar | O arquivo ZIP contém .shp, .shx, .dbf e .prj (WGS84). Ideal para QGIS/ArcGIS. |
| **KML** | Exportar/Importar | Formato nativo do Google Earth. |
| **CSV** | Exportar | Exporta os vértices das geometrias com coordenadas em **Decimal, UTM** e **Graus, Minutos, Segundos (DMS)**, incluindo o número do ponto. |

---

## 🛠️ Instalação e Execução (Docker)

A maneira recomendada para rodar o GIES é utilizando Docker e Docker Compose, garantindo que o ambiente Python e as bibliotecas GIS sejam configurados corretamente.

### Pré-requisitos
* Docker e Docker Compose instalados.

### Passos
1.  **Clone o Repositório** (ou garanta que todos os arquivos do projeto estão na mesma pasta).
2.  Abra o terminal na pasta raiz do projeto onde estão os arquivos `Dockerfile`, `docker-compose.yml` e `requirements.txt`.
3.  Execute o comando para construir a imagem e iniciar o serviço:

```bash
docker-compose up --build
```
4.  Acesse a aplicação no seu navegador: http://localhost:5000

💡 Nota sobre Persistência: O arquivo gies.db será criado no seu diretório local (./gies_project) e os dados serão mantidos mesmo após reiniciar o container, graças à configuração de volume no docker-compose.yml.