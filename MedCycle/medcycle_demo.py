# ============================================================
#  MEDCYCLE 2.1 — Autonomous Agentic Demo (Local Python Version)
#  Fully runnable, zero dependencies except:
#       pip install pandas scikit-learn sentence_transformers
#  Uses TF-IDF for semantic matching (no external models needed).
# ============================================================

import uuid
import random
from datetime import datetime, timedelta
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ------------------------------------------------------------
# Synthetic Data
# ------------------------------------------------------------
def create_inventory(n=25):
    meds = [
        ("Amoxicillin 500mg", "antibiotic bacterial infection"),
        ("Paracetamol 500mg", "analgesic fever pain"),
        ("Insulin Lispro", "insulin diabetes cold-chain"),
        ("Ceftriaxone 1g", "injectable antibiotic cold-chain"),
        ("Atorvastatin 20mg", "cholesterol chronic"),
        ("Salbutamol Inhaler", "asthma bronchodilator"),
        ("Vitamin B12 Injection", "vitamin injectable"),
        ("Metformin 500mg", "diabetes oral"),
        ("Rabies Vaccine", "vaccine cold-chain"),
    ]

    rows = []
    for i in range(n):
        name, desc = random.choice(meds)
        days = random.randint(5, 120)
        rows.append({
            "batch_id": f"BATCH-{1000+i}",
            "product": name,
            "description": desc,
            "days_to_expiry": days,
            "quantity": random.randint(10, 200),
            "unit_price": round(random.uniform(1, 80), 2),
            "location": random.choice(["Pune", "Mumbai", "Bengaluru", "Hyderabad"]),
            "cold_chain": "cold-chain" in desc,
        })
    return pd.DataFrame(rows)


def create_sites():
    return pd.DataFrame([
        {"site_id":"SITE-1","name":"Clinic A","location":"Pune","capacity":400,"profile":"general antibiotics analgesics"},
        {"site_id":"SITE-2","name":"Clinic B","location":"Mumbai","capacity":150,"profile":"maternal vaccines basic meds"},
        {"site_id":"SITE-3","name":"Hospital C","location":"Mumbai","capacity":2000,"profile":"critical care injectable antibiotics insulin"},
        {"site_id":"SITE-4","name":"Clinic D","location":"Bengaluru","capacity":300,"profile":"chronic diabetes hypertension"},
        {"site_id":"SITE-5","name":"Clinic E","location":"Hyderabad","capacity":200,"profile":"basic meds analgesics antibiotics"},
    ])


# ------------------------------------------------------------
# Vector Store (TF-IDF)
# ------------------------------------------------------------
class VectorStore:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.fitted = False

    def fit(self, texts):
        self.site_vecs = self.vectorizer.fit_transform(texts)
        self.fitted = True

    def sim(self, text):
        vec = self.vectorizer.transform([text])
        sims = cosine_similarity(vec, self.site_vecs)[0]
        return sims


# ------------------------------------------------------------
# Agents
# ------------------------------------------------------------
class InventoryScanner:
    def __init__(self, df):
        self.df = df

    def scan(self, threshold=90):
        return self.df[self.df.days_to_expiry <= threshold]


class ComplianceEngine:
    def check(self, batch, site):
        # simple rules for demo
        if batch["cold_chain"] and "injectable" not in site["profile"] and "vaccine" not in site["profile"]:
            return False, "SITE_HAS_NO_COLD_CHAIN"
        if batch["days_to_expiry"] <= 3:
            return False, "TOO_CLOSE_TO_EXPIRY"
        return True, None


class Planner:
    def __init__(self, sites):
        self.sites = sites
        self.store = VectorStore()
        self.store.fit(sites["profile"].astype(str).tolist())

    def rank(self, batch):
        text = batch["product"] + " " + batch["description"]
        sims = self.store.sim(text)

        scored = []
        for i, site in self.sites.iterrows():
            base = sims[i]
            if site["location"] == batch["location"]:
                base += 0.2
            scored.append((site, base))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored


class Executor:
    def __init__(self, inv_df):
        self.inv_df = inv_df
        self.audit = []

    def execute(self, batch, site):
        qty = min(batch["quantity"], int(site["capacity"] * 0.1))

        self.inv_df.loc[self.inv_df.batch_id == batch["batch_id"], "quantity"] -= qty

        record = {
            "dispatch_id": str(uuid.uuid4()),
            "batch_id": batch["batch_id"],
            "product": batch["product"],
            "to_site": site["name"],
            "qty": qty,
            "value": round(qty * batch["unit_price"], 2),
            "timestamp": datetime.utcnow(),
        }
        self.audit.append(record)
        return record


class Reporter:
    def summarize(self, audit_log):
        if not audit_log:
            return {"value_saved": 0, "co2_saved_kg": 0, "transfers": 0}

        value = sum(a["value"] for a in audit_log)
        units = sum(a["qty"] for a in audit_log)

        return {
            "value_saved": round(value, 2),
            "co2_saved_kg": round(units * 0.5, 2),
            "transfers": len(audit_log),
        }


# ------------------------------------------------------------
# Orchestrator
# ------------------------------------------------------------
class Orchestrator:
    def __init__(self, inventory, sites):
        self.inventory = inventory
        self.sites = sites

        self.scanner = InventoryScanner(inventory)
        self.compliance = ComplianceEngine()
        self.planner = Planner(sites)
        self.executor = Executor(inventory)
        self.reporter = Reporter()

    def run(self):
        candidates = self.scanner.scan()
        for _, batch in candidates.iterrows():
            ranked = self.planner.rank(batch)

            for site, score in ranked:
                ok, reason = self.compliance.check(batch, site)
                if ok and score > 0:
                    self.executor.execute(batch, site)
                    break

        return self.executor.audit


# ------------------------------------------------------------
# RUN DEMO
# ------------------------------------------------------------
if __name__ == "__main__":
    inventory = create_inventory()
    sites = create_sites()

    print("\n=== INITIAL INVENTORY ===")
    print(inventory.head())

    orch = Orchestrator(inventory, sites)
    audit = orch.run()

    print("\n=== AUDIT LOG ===")
    for a in audit:
        print(a)

    print("\n=== UPDATED INVENTORY ===")
    print(inventory.head())

    print("\n=== IMPACT REPORT ===")
    print(orch.reporter.summarize(audit))
