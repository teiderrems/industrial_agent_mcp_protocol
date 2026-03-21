# Makefile pour le projet Agent Industriel MCP
# Compatible Windows (GNU Make) et Unix/Linux

# Variables
VENV = venv
DB_PATH = industrial.db
ENV_FILE = .env
SERVER_SCRIPT = mcp_server.py
APP_SCRIPT = app.py

# Détection du système d'exploitation
ifeq ($(OS),Windows_NT)
    PYTHON = python
    VENV_PYTHON = $(VENV)\Scripts\python.exe
    VENV_PIP = $(VENV)\Scripts\pip.exe
    RM = del /q /f
    RMDIR = rmdir /s /q
    FIND = dir /s /b
    CAT = type
    SHELL = cmd.exe
    # Pour les commandes shell, on utilise cmd /c
    # On ajoute un backslash pour éviter les problèmes avec les espaces
    VENV_ACTIVATE = $(VENV)\Scripts\activate.bat
else
    PYTHON = python3
    VENV_PYTHON = $(VENV)/bin/python
    VENV_PIP = $(VENV)/bin/pip
    RM = rm -f
    RMDIR = rm -rf
    FIND = find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    CAT = cat
    VENV_ACTIVATE = . $(VENV)/bin/activate
endif

# Couleurs pour l'affichage (uniquement sur Unix)
ifeq ($(OS),Windows_NT)
    GREEN = 
    NC = 
else
    GREEN = \033[0;32m
    NC = \033[0m
endif

.PHONY: help install server app run clean reset db

help:
	@echo "$(GREEN)Makefile pour le projet Agent Industriel MCP$(NC)"
	@echo ""
	@echo "Commandes disponibles :"
	@echo "  install     Crée l'environnement virtuel et installe les dépendances"
	@echo "  server      Démarre le serveur MCP (FastMCP)"
	@echo "  app         Démarre l'interface Streamlit"
	@echo "  run         Démarre serveur et app en arrière-plan (exige tmux ou screen)"
	@echo "  db          Crée ou réinitialise la base de données mock (force)"
	@echo "  clean       Supprime les fichiers temporaires et le cache Python"
	@echo "  reset       Nettoie tout et réinstalle (équivalent clean + install)"
	@echo "  help        Affiche cette aide"

install: $(VENV)/bin/activate $(VENV)/Scripts/activate.bat
$(VENV)/bin/activate $(VENV)/Scripts/activate.bat: requirements.txt
	@echo "Création de l'environnement virtuel..."
	$(PYTHON) -m venv $(VENV)
	@echo "Installation des dépendances..."
	$(VENV_PIP) install -r requirements.txt
	@echo "Création du fichier .env à partir de .env.example (si inexistant)"
	@if not exist $(ENV_FILE) if exist .env.example copy .env.example $(ENV_FILE) > nul
	@echo "$(GREEN)Installation terminée.$(NC)"

server:
	@echo "Démarrage du serveur MCP..."
	$(VENV_PYTHON) $(SERVER_SCRIPT)

app:
	@echo "Démarrage de l'interface Streamlit..."
	$(VENV_PYTHON) -m streamlit run $(APP_SCRIPT)

run:
	@echo "Lancement des deux processus (serveur + Streamlit) dans des terminaux séparés."
	@echo "Utilisez 'make server' et 'make app' dans deux terminaux."
	@echo "Ou avec tmux/screen, exécutez :"
	@echo "  tmux new-session -d -s industrial 'make server'"
	@echo "  tmux split-window -h 'make app'"
	@echo "  tmux attach -t industrial"

db:
	@echo "Création / réinitialisation de la base de données mock..."
	$(VENV_PYTHON) -c "from mocks.mock_db import create_mock_db; create_mock_db('$(DB_PATH)', force=True)"
	@echo "$(GREEN)Base de données mock reconstruite.$(NC)"

clean:
	@echo "Nettoyage des fichiers temporaires et du cache..."
ifeq ($(OS),Windows_NT)
	@if exist __pycache__ rmdir /s /q __pycache__
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	@del /s /q *.pyc *.pyo *.pyd .DS_Store 2>nul
else
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@find . -type f -name ".DS_Store" -delete
endif
	@echo "$(GREEN)Nettoyage terminé.$(NC)"

reset: clean
	@echo "Réinitialisation complète : suppression de l'environnement virtuel et de la base..."
ifeq ($(OS),Windows_NT)
	@if exist $(VENV) rmdir /s /q $(VENV)
	@if exist $(DB_PATH) del /q $(DB_PATH)
else
	rm -rf $(VENV) $(DB_PATH) 2>/dev/null || true
endif
	@echo "$(GREEN)Exécutez 'make install' pour recommencer.$(NC)"

env:
	@echo "Variables d'environnement :"
	$(CAT) .env

api:
	@echo "Démarrage du serveur API FastAPI..."
	$(VENV_PYTHON) -m uvicorn api:app --reload --host 0.0.0.0 --port 8001

frontend:
	@echo "Démarrage de l'application React..."
	cd frontend && pnpm dev

# Optionnel : lancer tout (server MCP + API + frontend) en parallèle (nécessite tmux ou plusieurs terminaux)
run-all:
	@echo "Lancement de tous les services :"
	@echo "  - Serveur MCP (port 8000)"
	@echo "  - API FastAPI (port 8001)"
	@echo "  - Frontend React (port 3000)"
	@echo "Utilisez 'make server', 'make api', 'make frontend' dans des terminaux séparés."