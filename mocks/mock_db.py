# mocks/mock_db.py
import sqlite3
from datetime import datetime, timedelta
import random
import os

def create_mock_db(db_path="industrial.db", force=False):
    """Crée et peuple une base SQLite avec des données industrielles réalistes."""
    if not force and os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Suppression des tables existantes (pour recréer proprement)
    cursor.executescript("""
        DROP TABLE IF EXISTS mesures;
        DROP TABLE IF EXISTS capteurs;
        DROP TABLE IF EXISTS evenements_maintenance;
        DROP TABLE IF EXISTS machines;
    """)

    # Création des tables
    cursor.executescript("""
        CREATE TABLE machines (
            id_machine INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            type TEXT,
            date_installation DATE
        );

        CREATE TABLE capteurs (
            id_capteur INTEGER PRIMARY KEY AUTOINCREMENT,
            id_machine INTEGER,
            type_capteur TEXT,
            unite TEXT,
            FOREIGN KEY (id_machine) REFERENCES machines(id_machine)
        );

        CREATE TABLE mesures (
            id_mesure INTEGER PRIMARY KEY AUTOINCREMENT,
            id_capteur INTEGER,
            timestamp TIMESTAMP,
            valeur REAL,
            FOREIGN KEY (id_capteur) REFERENCES capteurs(id_capteur)
        );

        CREATE TABLE evenements_maintenance (
            id_evenement INTEGER PRIMARY KEY AUTOINCREMENT,
            id_machine INTEGER,
            date_debut TIMESTAMP,
            date_fin TIMESTAMP,
            description TEXT,
            FOREIGN KEY (id_machine) REFERENCES machines(id_machine)
        );
    """)

    # --- Insertion des machines ---
    machines_data = [
        ("Presse A", "Presse", "2020-01-01"),
        ("Tour B", "Tour", "2021-05-10"),
        ("Fraiseuse C", "Fraiseuse", "2022-03-20"),
        ("Robot D", "Robot", "2023-07-15"),
        ("Centrifugeuse E", "Centrifugeuse", "2020-11-01"),
        ("Compresseur F", "Compresseur", "2019-08-22"),
        ("Four G", "Four", "2021-12-10"),
        ("Mélangeur H", "Mélangeur", "2022-09-05"),
        ("Scie I", "Scie", "2023-01-30"),
        ("Nettoyeur J", "Nettoyeur", "2024-02-14"),
    ]
    cursor.executemany("INSERT INTO machines (nom, type, date_installation) VALUES (?, ?, ?)", machines_data)

    # Récupération des IDs machines
    cursor.execute("SELECT id_machine, nom FROM machines")
    machines = cursor.fetchall()

    # Types de capteurs avec unités
    capteur_types = [
        ("température", "°C"),
        ("vibration", "mm/s"),
        ("pression", "bar"),
    ]

    # Date de début des mesures (aujourd'hui - 89 jours)
    start_date = datetime.now().date() - timedelta(days=89)

    # Pour chaque machine, insérer les capteurs et les mesures
    for mid, mname in machines:
        for capteur_type, unite in capteur_types:
            # Insérer le capteur
            cursor.execute(
                "INSERT INTO capteurs (id_machine, type_capteur, unite) VALUES (?, ?, ?)",
                (mid, capteur_type, unite)
            )
            capteur_id = cursor.lastrowid

            # Générer les mesures sur 90 jours (start_date à start_date + 89)
            for i in range(90):
                ts = start_date + timedelta(days=i)
                # Valeurs réalistes selon le type de capteur
                if capteur_type == "température":
                    # Entre 15 et 85°C
                    valeur = random.uniform(15, 85)
                elif capteur_type == "vibration":
                    # Entre 0.1 et 15 mm/s
                    valeur = random.uniform(0.1, 15)
                else:  # pression
                    # Entre 1 et 10 bar
                    valeur = random.uniform(1, 10)
                # Ajouter une tendance ou un bruit ? Optionnel
                cursor.execute(
                    "INSERT INTO mesures (id_capteur, timestamp, valeur) VALUES (?, ?, ?)",
                    (capteur_id, ts, valeur)
                )

    # --- Événements de maintenance (10 événements aléatoires) ---
    maintenance_descriptions = [
        "Révision annuelle",
        "Changement d'huile",
        "Calibration des capteurs",
        "Remplacement de courroie",
        "Mise à jour logicielle",
        "Nettoyage en profondeur",
        "Contrôle de sécurité",
        "Réparation d'urgence",
        "Inspection trimestrielle",
        "Remplacement de pièce usée"
    ]
    # Dates aléatoires dans les 90 derniers jours
    for _ in range(10):
        # Choisir une machine aléatoire
        machine = random.choice(machines)
        mid = machine[0]
        # Date aléatoire dans les 90 derniers jours
        rand_days = random.randint(0, 89)
        debut = start_date + timedelta(days=rand_days)
        # Durée de l'intervention entre 1 et 8 heures
        duree = timedelta(hours=random.randint(1, 8))
        fin = debut + duree
        description = random.choice(maintenance_descriptions)
        cursor.execute(
            "INSERT INTO evenements_maintenance (id_machine, date_debut, date_fin, description) VALUES (?, ?, ?, ?)",
            (mid, debut, fin, description)
        )

    conn.commit()
    conn.close()
    print(f"Base de données mock créée avec succès : {db_path}")
    print(f" - Machines : {len(machines)}")
    print(f" - Capteurs : {len(machines) * len(capteur_types)}")
    print(f" - Mesures  : {len(machines) * len(capteur_types) * 90}")
    print(f" - Événements maintenance : 10")


def get_mock_db_connection(db_path="industrial.db"):
    """Retourne une connexion à la base SQLite."""
    return sqlite3.connect(db_path)