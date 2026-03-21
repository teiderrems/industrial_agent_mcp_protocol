# Industrial Agent LG

Agent industriel local utilisant FastMCP + LangGraph + LangChain + FastAPI.

## 🎯 Objectif

Ce projet propose une architecture d'agent capable de :
- recevoir une question en langage naturel via REST (`/ask`),
- convertir la question en requête SQL via LLM + outils MCP,
- exécuter la requête SQL sur une base (mock SQLite ou PostgreSQL),
- renvoyer la réponse enrichie (texte, SQL généré, résultats JSON).

## 📁 Structure du projet

- `api.py` : serveur FastAPI présidant le cycle de vie (lifespan) MCP + endpoint `/ask`.
- `mcp_client.py` : wrapper `IndustrialMCPClient` autour de `fastmcp.Client`.
- `mcp_tools.py` : implémente `MCPToolkit` et les outils `list_tables`, `describe_table`, `execute_sql_query`.
- `mcp_server.py` : serveur MCP (`FastMCP`) exposant les outils côté backend.
- `langgraph_agent.py` : construit le workflow agent LangGraph (modèle + outils).
- `app.py` : interface Streamlit pour usage direct local (fonctionnel mais optionnel selon le mode).
- `config.py` : configuration via `.env` (modes mock, connexions DB et LLM).
- `.env` : paramètres locaux pour DB, LLM, MCP_SERVER_URL.
- `frontend/` : interface web React + TypeScript.
- `mocks/` : génération de données mock et shémas de base.

## ⚙️ Prérequis

- Python 3.11+ / 3.12+ recommandé
- pip
- Node 18+ / pnpm (pour frontend)

## 🚀 Installation et démarrage

1. Cloner le dépôt et aller dans le dossier:

```bash
cd c:\Users\teide\Downloads\entretien\sogeti\industrial_agent_lg
```

2. Créer l'environnement virtuel et installer les dépendances:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

3. Vérifier ou copier `.env` (si pas présent) :

```bash
copy .env.example .env
```

4. Démarrer le serveur MCP:

```bash
venv\Scripts\python.exe mcp_server.py
```

5. Dans un autre terminal, démarrer l’API FastAPI:

```bash
venv\Scripts\python.exe -m uvicorn api:app --reload --host 0.0.0.0 --port 8001
```

6. Pour le frontend React :

```bash
cd frontend
pnpm install
pnpm dev
```

## 🧩 Configuration

Exemple `.env` (à adapter):

```ini
USE_MOCK_DB=true
USE_MOCK_LLM=true
MCP_SERVER_URL=http://127.0.0.1:8000
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3-flash-preview
MISTRAL_API_KEY=...
MISTRAL_MODEL=mistral-tiny
```

- `USE_MOCK_DB=true` : utilise SQLite mock (`industrial.db`) ; sinon PostgreSQL selon `POSTGRES_CONFIG`.
- `USE_MOCK_LLM=true` : bypass du LLM, sinon connexion aux clés définies.
- `MCP_SERVER_URL` : adresse du serveur MCP (ex: `http://127.0.0.1:8000`).

## 🧠 Flux principal

1. `api.py` / `/ask` -> convertit question en `HumanMessage`
2. `langgraph_agent.create_agent` -> workflow modélisation + outils
3. `mcp_tools` -> outils MCP utilisant `IndustrialMCPClient`
4. `mcp_client` -> envoie vers `fastmcp` (endpoint MCP)
5. `mcp_server` -> exécute SQL et renvoie résultats

## 🧪 Test manuel

- Requête via API:

```bash
curl -X POST "http://127.0.0.1:8001/ask" -H "Content-Type: application/json" -d "{\"question\": \"liste les tables\"}"
```

- UI React : `http://localhost:5173`.

- UI Streamlit : `http://localhost:8501`.

## 🛡️ Conseils de débogage

- Vérifier que `mcp_server` est bien sur `8000` (pas déjà occupé).
- Si `Session terminated` : c’est typiquement que `mcp_server` n’est pas démarré ou mauvaise URL.
- Activer logging compelete (FastAPI + MCP) pour tracer les échanges.

## 📦 Notes de développement

- Les docstrings ont été ajoutées dans `mcp_tools.py`, `mcp_client.py`, `mcp_server.py`, `langgraph_agent.py`, `api.py`.
- Le code est compatible avec l'architecture “mock first” (tous les outils sont testables sans services externes).

## 🧹 Nettoyage

```bash
venv\Scripts\deactivate
```

Supprimer la base SQLite (mock) si nécessaire:

```bash
del industrial.db
```

## 📝 Contributions

- Fork -> branche -> PR
- Inclure tests minimalistes si possible
- Documenter les variables `.env` ajoutées
