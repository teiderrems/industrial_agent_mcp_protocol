# mocks/mock_llm.py
import re
import json
import random

class MockLLM:
    def __init__(self):
        # Predefined Q&A pairs for demo
        self.qa_pairs = [
            (r"température moyenne.*machine (Presse A|Tour B|Fraiseuse C|Robot D)", 
             "SELECT AVG(m.valeur) FROM mesures m JOIN capteurs c ON m.id_capteur = c.id_capteur JOIN machines ma ON c.id_machine = ma.id_machine WHERE ma.nom = '{0}' AND c.type_capteur = 'température'"),
            (r"vibration.*max.*machine (Presse A|Tour B|Fraiseuse C|Robot D)",
             "SELECT MAX(m.valeur) FROM mesures m JOIN capteurs c ON m.id_capteur = c.id_capteur JOIN machines ma ON c.id_machine = ma.id_machine WHERE ma.nom = '{0}' AND c.type_capteur = 'vibration'"),
            (r"nombre d'arrêts.*maintenance", 
             "SELECT COUNT(*) FROM evenements_maintenance"),
            (r"liste.*capteurs", 
             "SELECT * FROM capteurs"),
            (r"production totale.*machine (Presse A|Tour B|Fraiseuse C|Robot D)",
             "SELECT COUNT(*) FROM mesures WHERE id_capteur IN (SELECT id_capteur FROM capteurs WHERE id_machine = (SELECT id_machine FROM machines WHERE nom = '{0}'))"),
        ]
    
    def generate_sql(self, question, schema_context=""):
        """Generate SQL based on predefined patterns."""
        for pattern, sql_template in self.qa_pairs:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                if match.groups():
                    # Replace placeholders
                    return sql_template.format(*match.groups())
                else:
                    return sql_template
        
        # Fallback: generic SQL based on keywords (simplified)
        return self._generic_sql(question, schema_context)
    
    def _generic_sql(self, question, schema_context):
        """Generate a simple SELECT based on keywords."""
        if "machine" in question.lower():
            return "SELECT * FROM machines LIMIT 10"
        elif "température" in question.lower():
            return "SELECT timestamp, valeur FROM mesures JOIN capteurs ON mesures.id_capteur = capteurs.id_capteur WHERE type_capteur = 'température' LIMIT 10"
        elif "vibration" in question.lower():
            return "SELECT timestamp, valeur FROM mesures JOIN capteurs ON mesures.id_capteur = capteurs.id_capteur WHERE type_capteur = 'vibration' LIMIT 10"
        elif "maintenance" in question.lower():
            return "SELECT * FROM evenements_maintenance LIMIT 10"
        else:
            return "SELECT * FROM machines LIMIT 5"