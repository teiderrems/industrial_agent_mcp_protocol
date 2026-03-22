import re
from typing import List, Dict, Any

class DecisionSimulator:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {
            "critical_columns": {
                "temperature": 85.0, "vibration": 12.0, "pressure": 10.0,
                "error_rate": 0.1, "downtime_minutes": 60, "rpm": 0, "status_code": 5
            },
            "warning_columns": {
                "temperature": 75.0, "vibration": 8.0, "pressure": 8.0,
                "error_rate": 0.05, "downtime_minutes": 30, "rpm": 100, "status_code": 3
            },
            "critical_keywords": ["failure", "stop", "crash", "overheat", "shutdown", "alarm", "critical"],
            "warning_keywords": ["warning", "high", "low", "degraded", "delay", "unstable"],
            "column_mappings": {
                "temperature": ["temperature", "temp", "température", "temperatura"],
                "vibration": ["vibration", "vib", "vibr", "oscillation"],
                "pressure": ["pressure", "pression", "press"],
                "error_rate": ["error_rate", "error rate", "taux d'erreur"],
                "downtime_minutes": ["downtime_minutes", "downtime", "temps d'arrêt"],
                "rpm": ["rpm", "rotations", "speed", "vitesse"],
                "status_code": ["status_code", "status", "code", "code_erreur"]
            }
        }

    def _map_column(self, col_name: str) -> str:
        """Map a column name to a standard metric key."""
        col_lower = col_name.lower()
        for standard, variants in self.config["column_mappings"].items():
            if any(variant in col_lower for variant in variants) or col_lower == standard:
                return standard
        return col_name  # fallback

    def simulate(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not results:
            return {
                "status": "no_data",
                "message": "Aucune donnée machine à analyser.",
                "details": {},
                "requires_human_intervention": False
            }

        # Check if any column maps to a known metric
        first_row = results[0]
        mapped_columns = [self._map_column(col) for col in first_row.keys()]
        relevant_columns = set(self.config["critical_columns"].keys()) | set(self.config["warning_columns"].keys())
        has_relevant = any(mapped in relevant_columns for mapped in mapped_columns)

        if not has_relevant:
            return {
                "status": "no_data",
                "message": "Les données ne contiennent pas de métriques machine.",
                "details": {},
                "requires_human_intervention": False
            }

        critical_count = 0
        warning_count = 0
        critical_reasons = []
        warning_reasons = []

        for row in results:
            for col, value in row.items():
                if not isinstance(value, (int, float)):
                    continue
                mapped = self._map_column(col)
                if mapped in self.config["critical_columns"]:
                    threshold = self.config["critical_columns"][mapped]
                    if value >= threshold:
                        critical_count += 1
                        critical_reasons.append(f"{col} = {value} >= {threshold}")
                    elif value >= self.config["warning_columns"].get(mapped, threshold):
                        warning_count += 1
                        warning_reasons.append(f"{col} = {value} >= {self.config['warning_columns'][mapped]}")

            # Keyword search in string columns
            for val in row.values():
                if isinstance(val, str):
                    val_lower = val.lower()
                    for kw in self.config["critical_keywords"]:
                        if kw in val_lower:
                            critical_count += 1
                            critical_reasons.append(f"Mot-clé critique: '{kw}'")
                            break
                    for kw in self.config["warning_keywords"]:
                        if kw in val_lower:
                            warning_count += 1
                            warning_reasons.append(f"Mot-clé d'alerte: '{kw}'")
                            break

        if critical_count > 0:
            status = "critical"
            message = f"🔴 {critical_count} alerte(s) critique(s) détectée(s) – intervention immédiate nécessaire."
            human = True
        elif warning_count > 0:
            status = "warning"
            message = f"🟠 {warning_count} alerte(s) préventive(s) détectée(s) – surveiller la situation."
            human = False
        else:
            status = "normal"
            message = "🟢 Aucune anomalie détectée – situation normale."
            human = False

        return {
            "status": status,
            "message": message,
            "details": {
                "critical_count": critical_count,
                "warning_count": warning_count,
                "critical_reasons": list(set(critical_reasons))[:5],
                "warning_reasons": list(set(warning_reasons))[:5],
            },
            "requires_human_intervention": human,
        }