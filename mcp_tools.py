import asyncio
import json
from typing import Type
from langchain_core.tools import StructuredTool
from pydantic import BaseModel
from mcp_client import IndustrialMCPClient
import config
import nest_asyncio
from decision_simulator import DecisionSimulator   # new import

nest_asyncio.apply()

class ExecuteSQLInput(BaseModel):
    query: str

class DescribeTableInput(BaseModel):
    table_name: str

class SimulateDecisionInput(BaseModel):   # new input schema
    results: list

class MCPToolkit:
    """Wrapper de connexion au serveur MCP et outils exposés pour l'agent.

    La classe gère un client unique (`IndustrialMCPClient`) et assure l'ouverture
    et la fermeture du contexte asynchrone sur la durée de vie de l'application.
    Elle expose un ensemble de fonctions `StructuredTool` pour les opérations
    SQL de lecture (list_tables, describe_table, execute_sql_query) et
    pour la simulation de décision (simulate_decision).
    """

    def __init__(self, server_url: str = config.MCP_SERVER_URL):
        """Initialise l'outil avec l'URL du serveur MCP.

        Args:
            server_url (str): adresse du serveur MCP (ex: http://127.0.0.1:8000).
        """
        self.server_url = server_url
        self._client = None

    async def _get_client(self):
        """Récupère et initialise le client MCP.

        Si aucun client n'est initialisé, crée un `IndustrialMCPClient` via
        `server_url`, puis appelle `__aenter__()` pour établir la session.

        Returns:
            IndustrialMCPClient: client MCP prêt à l'emploi.
        """
        if self._client is None:
            self._client = IndustrialMCPClient(self.server_url)
            await self._client.__aenter__()
        return self._client

    async def _close_client(self):
        """Ferme proprement la connexion MCP si elle existe."""
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None

    def get_tools(self):
        async def list_tables():
            """Outil MCP: liste toutes les tables de la base de données.

            Utilise la méthode `list_tables` du client MCP pour récupérer les
            informations de schéma puis renvoie le résultat formaté JSON.

            Returns:
                str: JSON indenté de la liste des tables.
            """
            client = await self._get_client()
            tables = await client.get_tables()
            return json.dumps(tables, indent=2)

        async def describe_table(table_name: str):
            """Outil MCP: description du schéma d'une table spécifique.

            Args:
                table_name (str): nom de la table à décrire.

            Returns:
                str: JSON indenté de la description de la table.
            """
            client = await self._get_client()
            result = await client.describe_table(table_name)
            return json.dumps(result, indent=2)

        async def execute_sql(query: str):
            """Outil MCP: exécute une requête SQL SELECT et renvoie le résultat.

            Args:
                query (str): requête SQL (seulement SELECT autorisées côté serveur).

            Returns:
                str: résultat de la requête (JSON ou message d'erreur JSON).
            """
            client = await self._get_client()
            result = await client.query(query)
            return result

        # Nouvel outil : simulation de décision
        async def simulate_decision(results: list):
            """Outil MCP (local) : simule une décision à partir des résultats d'une requête SQL.

            Args:
                results (list): liste des résultats (dictionnaires) retournés par `execute_sql_query`.

            Returns:
                str: JSON de la décision (status, message, details, intervention).
            """
            simulator = DecisionSimulator()
            decision = simulator.simulate(results)
            return json.dumps(decision, indent=2, default=str)

        tools = [
            StructuredTool.from_function(
                coroutine=list_tables,
                name="list_tables",
                description="Liste toutes les tables disponibles dans la base de données.",
                args_schema=BaseModel,
            ),
            StructuredTool.from_function(
                coroutine=describe_table,
                name="describe_table",
                description="Retourne la structure d'une table (colonnes, types, etc.).",
                args_schema=DescribeTableInput,
            ),
            StructuredTool.from_function(
                coroutine=execute_sql,
                name="execute_sql_query",
                description="Exécute une requête SQL SELECT et retourne les résultats.",
                args_schema=ExecuteSQLInput,
            ),
            StructuredTool.from_function(
                coroutine=simulate_decision,
                name="simulate_decision",
                description="Simule une décision (critical/warning/normal) à partir des résultats d'une requête SQL.",
                args_schema=SimulateDecisionInput,
            ),
        ]
        return tools


# import asyncio
# import json
# from typing import Type
# from langchain_core.tools import StructuredTool
# from pydantic import BaseModel
# from mcp_client import IndustrialMCPClient
# import config
# import nest_asyncio

# nest_asyncio.apply()

# class ExecuteSQLInput(BaseModel):
#     query: str

# class DescribeTableInput(BaseModel):
#     table_name: str

# class MCPToolkit:
#     """Wrapper de connexion au serveur MCP et outils exposés pour l'agent.

#     La classe gère un client unique (`IndustrialMCPClient`) et assure l'ouverture
#     et la fermeture du contexte asynchrone sur la durée de vie de l'application.
#     Elle expose un ensemble de fonctions `StructuredTool` pour les opérations
#     SQL de lecture (list_tables, describe_table, execute_sql_query).
#     """

#     def __init__(self, server_url: str = config.MCP_SERVER_URL):
#         """Initialise l'outil avec l'URL du serveur MCP.

#         Args:
#             server_url (str): adresse du serveur MCP (ex: http://127.0.0.1:8000).
#         """
#         self.server_url = server_url
#         self._client = None

#     async def _get_client(self):
#         """Récupère et initialise le client MCP.

#         Si aucun client n'est initialisé, crée un `IndustrialMCPClient` via
#         `server_url`, puis appelle `__aenter__()` pour établir la session.

#         Returns:
#             IndustrialMCPClient: client MCP prêt à l'emploi.
#         """
#         if self._client is None:
#             self._client = IndustrialMCPClient(self.server_url)
#             await self._client.__aenter__()
#         return self._client

#     async def _close_client(self):
#         """Ferme proprement la connexion MCP si elle existe."""
#         if self._client:
#             await self._client.__aexit__(None, None, None)
#             self._client = None

#     def get_tools(self):
#         async def list_tables():
#             """Outil MCP: liste toutes les tables de la base de données.

#             Utilise la méthode `list_tables` du client MCP pour récupérer les
#             informations de schéma puis renvoie le résultat formaté JSON.

#             Returns:
#                 str: JSON indenté de la liste des tables.
#             """
#             client = await self._get_client()
#             tables = await client.get_tables()
#             return json.dumps(tables, indent=2)

#         async def describe_table(table_name: str):
#             """Outil MCP: description du schéma d'une table spécifique.

#             Args:
#                 table_name (str): nom de la table à décrire.

#             Returns:
#                 str: JSON indenté de la description de la table.
#             """
#             client = await self._get_client()
#             result = await client.describe_table(table_name)
#             return json.dumps(result, indent=2)

#         async def execute_sql(query: str):
#             """Outil MCP: exécute une requête SQL SELECT et renvoie le résultat.

#             Args:
#                 query (str): requête SQL (seulement SELECT autorisées côté serveur).

#             Returns:
#                 str: résultat de la requête (JSON ou message d'erreur JSON).
#             """
#             client = await self._get_client()
#             result = await client.query(query)
#             return result

#         tools = [
#             StructuredTool.from_function(
#                 coroutine=list_tables,
#                 name="list_tables",
#                 description="Liste toutes les tables disponibles dans la base de données.",
#                 args_schema=BaseModel,
#             ),
#             StructuredTool.from_function(
#                 coroutine=describe_table,
#                 name="describe_table",
#                 description="Retourne la structure d'une table (colonnes, types, etc.).",
#                 args_schema=DescribeTableInput,
#             ),
#             StructuredTool.from_function(
#                 coroutine=execute_sql,
#                 name="execute_sql_query",
#                 description="Exécute une requête SQL SELECT et retourne les résultats.",
#                 args_schema=ExecuteSQLInput,
#             ),
#         ]
#         return tools