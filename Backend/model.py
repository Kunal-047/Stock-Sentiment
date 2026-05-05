"""
model.py — Phase 4 Serving Layer
Loads champion_model.pkl once at startup.
Exposes predict() and shap_contributions() used by the API routes.
"""

import pickle
import warnings
from pathlib import Path
from typing import Optional

import numpy as np
import shap

warnings.filterwarnings("ignore")

# Singleton state — populated by load_model() at startup
_pipeline      = None
_label_encoder = None
_feature_cols  = None
_explainer     = None
_model_path    = None


def load_model(path: str) -> None:
    """
    Call once at app startup.
    Loads the champion_model.pkl written by Phase 3 and initialises
    the SHAP TreeExplainer against the XGBoost clf step.
    """
    global _pipeline, _label_encoder, _feature_cols, _explainer, _model_path

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"Champion model not found at '{path}'. "
            "Run Phase 3 on Kaggle and copy champion_model.pkl here."
        )

    with open(p, "rb") as f:
        bundle = pickle.load(f)

    _pipeline      = bundle["pipeline"]
    _label_encoder = bundle["label_encoder"]
    _feature_cols  = bundle["feature_cols"]
    _model_path    = str(p)

    # Initialise SHAP explainer on the raw XGBoost clf (post-pipeline transform)
    xgb_clf    = _pipeline.named_steps["clf"]
    _explainer = shap.TreeExplainer(xgb_clf)

    n_classes = len(_label_encoder.classes_)
    print(
        f"[model] ✅ Loaded: {p.name}  |  "
        f"features={len(_feature_cols)}  |  classes={n_classes}"
    )


def is_loaded() -> bool:
    return _pipeline is not None


def get_model_path() -> Optional[str]:
    return _model_path


def _transform(feature_dict: dict) -> np.ndarray:
    """
    Applies the pipeline's imputer + scaler to a single feature row.
    Returns a 2-D array (1, n_features) ready for the clf step.
    """
    import pandas as pd
    row = pd.DataFrame([{col: feature_dict.get(col, 0.0) for col in _feature_cols}])
    X   = row.values.astype(np.float32)

    # Apply imputer + scaler steps only (not the final clf)
    for name, step in _pipeline.steps[:-1]:
        X = step.transform(X)
    return X


def predict(feature_dict: dict) -> dict:
    """
    Runs the full pipeline on one feature row.

    Returns:
        prediction      : str  — "Up" / "Flat" / "Down"
        predicted_class : int  — original label (-1 / 0 / 1)
        confidence      : float — max class probability (0–1)
        probabilities   : dict  — {"Down": p, "Flat": p, "Up": p}
    """
    import pandas as pd

    row = pd.DataFrame([{col: feature_dict.get(col, 0.0) for col in _feature_cols}])
    X   = row.values.astype(np.float32)

    proba       = _pipeline.predict_proba(X)[0]          # shape (n_classes,)
    encoded_cls = int(np.argmax(proba))
    orig_label  = int(_label_encoder.inverse_transform([encoded_cls])[0])

    label_map   = {-1: "Down", 0: "Flat", 1: "Up"}
    class_names = [label_map[int(c)] for c in _label_encoder.classes_]

    return {
        "prediction":      label_map[orig_label],
        "predicted_class": orig_label,
        "confidence":      float(np.max(proba)),
        "probabilities":   dict(zip(class_names, proba.tolist())),
    }


def shap_contributions(feature_dict: dict, top_n: int = 10) -> list[dict]:
    """
    Returns SHAP feature contributions for the predicted class.

    For multi-class XGBoost, shap_values is a list of arrays,
    one per class.  We report values for the predicted (argmax) class.

    Returns list of dicts sorted by |shap_value| descending:
        [{"feature": str, "value": float, "shap": float}, ...]
    """
    import pandas as pd

    row = pd.DataFrame([{col: feature_dict.get(col, 0.0) for col in _feature_cols}])
    X   = row.values.astype(np.float32)

    # Transform through imputer + scaler before SHAP (explainer sees clf input)
    X_transformed = _transform(feature_dict)

    raw = _explainer.shap_values(X_transformed)   # list[array] or array

    # Determine predicted class index
    proba       = _pipeline.predict_proba(X)[0]
    encoded_cls = int(np.argmax(proba))

    # raw is list of (1, n_features) arrays, one per class
    if isinstance(raw, list):
        shap_row = raw[encoded_cls][0]
    else:
        # Binary case — shouldn't happen for 3-class but guard anyway
        shap_row = raw[0]

    contributions = []
    for i, col in enumerate(_feature_cols):
        contributions.append({
            "feature": col,
            "value":   float(feature_dict.get(col, 0.0)),
            "shap":    float(shap_row[i]),
        })

    contributions.sort(key=lambda x: abs(x["shap"]), reverse=True)
    return contributions[:top_n]
