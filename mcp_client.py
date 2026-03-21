import json
from fastmcp import Client

class IndustrialMCPClient:
    """Client wrapper pour communiquer avec le serveur MCP.

    Cette classe encapsule `fastmcp.Client` et fournit un contexte
    asynchrone (`__aenter__`/`__aexit__`) pour gérer la connexion.
    Elle expose des méthodes de plus haut niveau pour effectuer des
    outils MCP définis par le serveur.
    """

    def __init__(self, server_url: str):
        """Initialise le client MCP.

        Args:
            server_url (str): URL du serveur MCP (ex: http://127.0.0.1:8000).
        """
        self.server_url = server_url
        self.client = None

    async def __aenter__(self):
        """Ouvre une session MCP asynchrone.

        Instancie `fastmcp.Client` et appelle son `__aenter__` pour établir
        la connexion avec le serveur.

        Returns:
            IndustrialMCPClient: l'objet client actif.
        """
        # Utiliser le transport HTTP explicite pour streamable-http
        self.client = Client(self.server_url)
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ferme proprement la session MCP."""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def get_tables(self):
        """Récupère la liste des tables disponibles via MCP."""
        result = await self.client.call_tool("list_tables", {})
        return json.loads(result.content[0].text)

    async def describe_table(self, table_name: str):
        """Décrit une table existante.

        Args:
            table_name (str): nom de la table à décrire.
        """
        result = await self.client.call_tool("describe_table", {"table_name": table_name})
        return json.loads(result.content[0].text)

    async def query(self, sql_query: str):
        """Exécute une requête SQL SELECT et renvoie le résultat brut JSON.

        Args:
            sql_query (str): requête SQL (filtrée côté serveur pour être SELECT).

        Returns:
            str: texte JSON retourné par le serveur MCP.
        """
        result = await self.client.call_tool("execute_sql_query", {"query": sql_query})
        return result.content[0].text