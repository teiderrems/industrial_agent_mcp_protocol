import os
import json
import sqlite3
import asyncio
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from fastmcp import FastMCP, Context
import config

mcp = FastMCP("Industrial Database Server")

def get_db_connection():
    """Retourne une connexion à la base de données.

    En mode mock (`USE_MOCK_DB=true`) :
      - crée la base SQLite mock si nécessaire
      - ouvre `sqlite3` sur le fichier configuré

    En mode production :
      - ouvre une connexion PostgreSQL via `psycopg2`.

    Returns:
        sqlite3.Connection | psycopg2.extensions.connection | None
    """
    if config.USE_MOCK_DB:
        try:
            if not os.path.exists(config.SQLITE_DB_PATH):
                from mocks.mock_db import create_mock_db
                create_mock_db(config.SQLITE_DB_PATH, force=True)
            conn = sqlite3.connect(config.SQLITE_DB_PATH)
            return conn
        except Exception as e:
            print(f"SQLite connection error: {e}")
            return None
    else:
        try:
            return psycopg2.connect(**config.POSTGRES_CONFIG)
        except Exception as e:
            print(f"PostgreSQL connection error: {e}")
            return None

@mcp.tool(description="Exécute une requête SQL SELECT et retourne les résultats.")
async def execute_sql_query(query: str, ctx: Context) -> str:
    """Exécute une requête SQL en lecture via MCP.

    La fonction accepte uniquement les requêtes commençant par SELECT.
    En mode mock, elle utilise SQLite et renvoie une liste de dict.
    En mode production, elle utilise PostgreSQL et RealDictCursor.

    Args:
        query (str): requête SQL à exécuter (doit être SELECT).
        ctx (Context): contexte MCP (inclus par decorator mcp.tool).

    Returns:
        str: JSON stringifié du résultat ou message d'erreur.
    """
    if not query.strip().upper().startswith("SELECT"):
        return json.dumps({"error": "Only SELECT queries are allowed."})
    conn = None
    try:
        conn = get_db_connection()
        if conn is None:
            return json.dumps({"error": "Database connection failed."})
        cursor = conn.cursor()
        cursor.execute(query)
        if config.USE_MOCK_DB:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            results = [dict(zip(columns, row)) for row in rows]
        else:
            # PostgreSQL avec RealDictCursor
            conn2 = get_db_connection()
            cursor2 = conn2.cursor(cursor_factory=RealDictCursor)
            cursor2.execute(query)
            results = cursor2.fetchall()
            conn2.close()
        return json.dumps(results, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if conn:
            conn.close()

@mcp.tool(description="Liste toutes les tables disponibles.")
async def list_tables(ctx: Context) -> str:
    """Retourne la liste des tables définies dans la base de données.

    Args:
        ctx (Context): contexte MCP.

    Returns:
        str: JSON contenant le résultat de la requête de métadonnées.
    """
    if config.USE_MOCK_DB:
        return await execute_sql_query("SELECT name FROM sqlite_master WHERE type='table'", ctx)
    else:
        return await execute_sql_query(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public'", ctx
        )

@mcp.tool(description="Décrit la structure d'une table.")
async def describe_table(table_name: str, ctx: Context) -> str:
    """Retourne les colonnes et types pour une table donnée.

    Args:
        table_name (str): nom de la table à inspecter.
        ctx (Context): contexte MCP.

    Returns:
        str: JSON de la structure des colonnes.
    """
    if config.USE_MOCK_DB:
        return await execute_sql_query(f"PRAGMA table_info({table_name})", ctx)
    else:
        # PostgreSQL – correction : utiliser une requête paramétrée
        # Note: Pour éviter l'injection SQL, nous utilisons psycopg2.sql.
        # Mais comme execute_sql_query ne prend pas encore de paramètres, nous construisons la requête.
        # Une meilleure approche serait d'ajouter un mécanisme de paramètres dans execute_sql_query.
        query = sql.SQL("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema='public' AND table_name = {}
        """).format(sql.Literal(table_name))
        return await execute_sql_query(query.as_string(psycopg2), ctx)

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8000, path="/")



# import os
# import json
# import sqlite3
# import asyncio
# import psycopg2
# from psycopg2 import sql
# from psycopg2.extras import RealDictCursor
# from fastmcp import FastMCP, Context
# import config

# mcp = FastMCP("Industrial Database Server")

# def get_db_connection():
#     """Retourne une connexion à la base de données.

#     En mode mock (`USE_MOCK_DB=true`) :
#       - crée la base SQLite mock si nécessaire
#       - ouvre `sqlite3` sur le fichier configuré

#     En mode production :
#       - ouvre une connexion PostgreSQL via `psycopg2`.

#     Returns:
#         sqlite3.Connection | psycopg2.extensions.connection | None
#     """
#     if config.USE_MOCK_DB:
#         try:
#             if not os.path.exists(config.SQLITE_DB_PATH):
#                 from mocks.mock_db import create_mock_db
#                 create_mock_db(config.SQLITE_DB_PATH, force=True)
#             conn = sqlite3.connect(config.SQLITE_DB_PATH)
#             return conn
#         except Exception as e:
#             print(f"SQLite connection error: {e}")
#             return None
#     else:
#         try:
#             return psycopg2.connect(**config.POSTGRES_CONFIG)
#         except Exception as e:
#             print(f"PostgreSQL connection error: {e}")
#             return None

# @mcp.tool(description="Exécute une requête SQL SELECT et retourne les résultats.")
# async def execute_sql_query(query: str, ctx: Context) -> str:
#     """Exécute une requête SQL en lecture via MCP.

#     La fonction accepte uniquement les requêtes commençant par SELECT.
#     En mode mock, elle utilise SQLite et renvoie une liste de dict.
#     En mode production, elle utilise PostgreSQL et RealDictCursor.

#     Args:
#         query (str): requête SQL à exécuter (doit être SELECT).
#         ctx (Context): contexte MCP (inclus par decorator mcp.tool).

#     Returns:
#         str: JSON stringifié du résultat ou message d'erreur.
#     """
#     if not query.strip().upper().startswith("SELECT"):
#         return json.dumps({"error": "Only SELECT queries are allowed."})
#     conn = None
#     try:
#         conn = get_db_connection()
#         if conn is None:
#             return json.dumps({"error": "Database connection failed."})
#         cursor = conn.cursor()
#         cursor.execute(query)
#         if config.USE_MOCK_DB:
#             columns = [desc[0] for desc in cursor.description]
#             rows = cursor.fetchall()
#             results = [dict(zip(columns, row)) for row in rows]
#         else:
#             # PostgreSQL avec RealDictCursor
#             conn2 = get_db_connection()
#             cursor2 = conn2.cursor(cursor_factory=RealDictCursor)
#             cursor2.execute(query)
#             results = cursor2.fetchall()
#             conn2.close()
#         return json.dumps(results, indent=2, default=str)
#     except Exception as e:
#         return json.dumps({"error": str(e)})
#     finally:
#         if conn:
#             conn.close()

# @mcp.tool(description="Liste toutes les tables disponibles.")
# async def list_tables(ctx: Context) -> str:
#     """Retourne la liste des tables définies dans la base de données.

#     Args:
#         ctx (Context): contexte MCP.

#     Returns:
#         str: JSON contenant le résultat de la requête de métadonnées.
#     """
#     if config.USE_MOCK_DB:
#         return await execute_sql_query("SELECT name FROM sqlite_master WHERE type='table'", ctx)
#     else:
#         return await execute_sql_query("SELECT table_name FROM information_schema.tables WHERE table_schema='public'", ctx)


# @mcp.tool(description="Décrit la structure d'une table.")
# async def describe_table(table_name: str, ctx: Context) -> str:
#     """Retourne les colonnes et types pour une table donnée.

#     Args:
#         table_name (str): nom de la table à inspecter.
#         ctx (Context): contexte MCP.

#     Returns:
#         str: JSON de la structure des colonnes.
#     """
#     if config.USE_MOCK_DB:
#         return await execute_sql_query(f"PRAGMA table_info({table_name})", ctx)
#     else:
#         # Remarque : pour PostgreSQL, la requête actuelle n'utilise pas correctement la valeur table_name.
#         return await execute_sql_query(sql.SQL("""
#             SELECT column_name, data_type, is_nullable
#             FROM information_schema.columns
#             WHERE table_schema='public' AND table_name=%s
#         """).as_string(psycopg2), ctx)  # Note: à améliorer


# if __name__ == "__main__":
#     mcp.run(transport="streamable-http", host="127.0.0.1", port=8000, path="/")