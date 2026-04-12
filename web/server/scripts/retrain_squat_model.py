"""
Retrain the squat counter model using the existing training data.
The original model was a RandomForestClassifier trained with sklearn 1.1.2
which is incompatible with sklearn 1.6.1 (DecisionTree node dtype changed in 1.3+).

This script reads the training CSV and retrains the model, then saves it to
the static model path used by the Django server.
"""
import os
import sys
import pickle
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.dirname(SCRIPT_DIR)
REPO_ROOT  = os.path.dirname(os.path.dirname(SERVER_DIR))

TRAIN_CSV  = os.path.join(REPO_ROOT, "core", "squat_model", "train.csv")
TEST_CSV   = os.path.join(REPO_ROOT, "core", "squat_model", "test.csv")
OUTPUT_PKL = os.path.join(SERVER_DIR, "static", "model", "squat_model.pkl")

print(f"Train CSV : {TRAIN_CSV}")
print(f"Test  CSV : {TEST_CSV}")
print(f"Output    : {OUTPUT_PKL}")

# ── Load data ──────────────────────────────────────────────────────────────────
print("\nLoading training data…")
df_train = pd.read_csv(TRAIN_CSV)
df_test  = pd.read_csv(TEST_CSV)

print(f"  Train shape : {df_train.shape}")
print(f"  Test  shape : {df_test.shape}")
print(f"  Train labels: {df_train['label'].value_counts().to_dict()}")

X_train = df_train.drop("label", axis=1)
y_train = df_train["label"]
X_test  = df_test.drop("label", axis=1)
y_test  = df_test["label"]

# ── Train model ────────────────────────────────────────────────────────────────
print("\nTraining RandomForestClassifier…")
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=None,
    random_state=42,
    n_jobs=-1,
)
model.fit(X_train, y_train)

# ── Evaluate ───────────────────────────────────────────────────────────────────
y_pred = model.predict(X_test)
acc    = accuracy_score(y_test, y_pred)
print(f"\nTest Accuracy: {acc:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# ── Save ───────────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUTPUT_PKL), exist_ok=True)
with open(OUTPUT_PKL, "wb") as f:
    pickle.dump(model, f)

print(f"\nModel saved to: {OUTPUT_PKL}")

# Quick verification
with open(OUTPUT_PKL, "rb") as f:
    loaded = pickle.load(f)
sample  = X_test.iloc[:3]
pred    = loaded.predict(sample)
proba   = loaded.predict_proba(sample)
print(f"\nVerification – predictions on 3 samples: {pred}")
print(f"Probabilities:\n{proba}")
print("\nDone! ✓")
