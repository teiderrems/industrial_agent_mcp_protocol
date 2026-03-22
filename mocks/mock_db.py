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

    # Suppression des tables existantes
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

    # --- Insertion des machines (10 machines) ---
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

    cursor.execute("SELECT id_machine, nom FROM machines")
    machines = cursor.fetchall()

    # Types de capteurs avec unités
    capteur_types = [
        ("température", "°C"),
        ("vibration", "mm/s"),
        ("pression", "bar"),
    ]

    start_date = datetime.now().date() - timedelta(days=89)

    # Pour chaque machine, insérer les capteurs et les mesures
    for mid, mname in machines:
        # Assigner des tendances spécifiques pour certaines machines
        # Par exemple, machine "Presse A" aura des températures élevées
        if mname == "Presse A":
            temp_range = (75, 95)   # warning/critical
            vib_range = (8, 15)     # warning/critical
            press_range = (7, 11)   # warning/critical
        elif mname == "Tour B":
            temp_range = (70, 88)
            vib_range = (7, 14)
            press_range = (6, 10)
        elif mname == "Compresseur F":
            temp_range = (80, 98)   # very high
            vib_range = (10, 18)
            press_range = (8, 12)
        else:
            # normal range (safe)
            temp_range = (20, 70)
            vib_range = (0.5, 7)
            press_range = (2, 6)

        for capteur_type, unite in capteur_types:
            cursor.execute(
                "INSERT INTO capteurs (id_machine, type_capteur, unite) VALUES (?, ?, ?)",
                (mid, capteur_type, unite)
            )
            capteur_id = cursor.lastrowid

            # Générer les mesures sur 90 jours
            for i in range(90):
                ts = start_date + timedelta(days=i)
                if capteur_type == "température":
                    valeur = random.uniform(*temp_range)
                elif capteur_type == "vibration":
                    valeur = random.uniform(*vib_range)
                else:  # pression
                    valeur = random.uniform(*press_range)
                cursor.execute(
                    "INSERT INTO mesures (id_capteur, timestamp, valeur) VALUES (?, ?, ?)",
                    (capteur_id, ts, valeur)
                )

    # --- Événements de maintenance avec mots-clés critiques/alerte ---
    maintenance_events = [
        ("Révision annuelle", "normal"),
        ("Changement d'huile", "normal"),
        ("Calibration des capteurs", "normal"),
        ("Remplacement de courroie", "warning"),
        ("Mise à jour logicielle", "normal"),
        ("Nettoyage en profondeur", "normal"),
        ("Contrôle de sécurité", "normal"),
        ("Réparation d'urgence", "critical"),
        ("Inspection trimestrielle", "normal"),
        ("Remplacement de pièce usée", "warning"),
        ("ALARME : surchauffe détectée", "critical"),
        ("Arrêt d'urgence suite à défaillance", "critical"),
        ("Vibration excessive - maintenance requise", "warning"),
        ("Fuite de pression critique", "critical"),
        ("Stop machine pour surchauffe", "critical"),
    ]

    # Créer des événements pour les machines problématiques
    problematic_machines = [m for m in machines if m[1] in ["Presse A", "Tour B", "Compresseur F"]]
    for _ in range(15):
        # Choisir une machine (problématique plus souvent)
        if random.random() < 0.7 and problematic_machines:
            machine = random.choice(problematic_machines)
        else:
            machine = random.choice(machines)
        mid = machine[0]
        # Date aléatoire dans les 90 derniers jours
        rand_days = random.randint(0, 89)
        debut = start_date + timedelta(days=rand_days)
        duree = timedelta(hours=random.randint(1, 8))
        fin = debut + duree
        desc, severity = random.choice(maintenance_events)
        if severity == "critical":
            # Ajouter un mot-clé critique si pas déjà présent
            if not any(kw in desc.lower() for kw in ["critical", "alarme", "arrêt", "défaillance", "surchauffe", "stop"]):
                desc = "CRITIQUE: " + desc
        elif severity == "warning":
            if not any(kw in desc.lower() for kw in ["warning", "excessive", "requise"]):
                desc = "AVERTISSEMENT: " + desc
        cursor.execute(
            "INSERT INTO evenements_maintenance (id_machine, date_debut, date_fin, description) VALUES (?, ?, ?, ?)",
            (mid, debut, fin, desc)
        )

    conn.commit()
    conn.close()
    print(f"Base de données mock créée avec succès : {db_path}")
    print(f" - Machines : {len(machines)}")
    print(f" - Capteurs : {len(machines) * len(capteur_types)}")
    print(f" - Mesures  : {len(machines) * len(capteur_types) * 90}")
    print(f" - Événements maintenance : 15 (incluant mots-clés critiques/alerte)")


def get_mock_db_connection(db_path="industrial.db"):
    """Retourne une connexion à la base SQLite."""
    return sqlite3.connect(db_path)