# AI Risk Service

AI Risk Service is a production-oriented ML microservice for real-time insurance risk intelligence.

It is designed to power premium pricing, claims risk context, and fraud-sensitive decisions.

---

## 1) What This Service Provides

### Core runtime outputs

For each inference request, the service returns:

1. Continuous risk score in range [0, 1]
2. Risk category (`LOW`, `MEDIUM`, `HIGH`) using deterministic thresholds
3. Premium multiplier
4. Confidence score
5. Top contributing factors (lightweight explainability)
6. Prediction id for Human-in-the-Loop feedback tracking

### Operational capabilities

1. JWT auth + RBAC + request-id + rate limiting
2. Hybrid risk engine (`70%` ML + `30%` deterministic rule layer)
3. Drift diagnostics against training baselines
4. Feedback ingestion APIs for retraining loop
5. Model registry with active-artifact switching
6. Fallback heuristic model for resiliency if artifact loading fails

---

## 2) High-Level Architecture

```text
Client
	-> FastAPI API Layer
			-> Security + Validation + Rate Limiting
			-> Feature Builder (base + engineered + temporal)
			-> Hybrid Risk Engine
					-> ML Regressor (RandomForest)
					-> Rule Engine
			-> Confidence + Explainability
			-> Prediction Logging (HITL)
			-> Response Envelope

Offline ML Pipeline
	-> Scenario/Correlated Synthetic Data
	-> Preprocess + Feature Engineering
	-> Train + Cross-Validate + Evaluate
	-> Feature Importance Validation
	-> Metadata + Model Registry + Versioned Artifact
	-> Visual QA Reports
```

---

## 3) API Endpoints

### POST `/api/v1/risk/evaluate`

Predict risk using metrics and optional temporal context.

### GET `/api/v1/risk/health`

Service health, model load state, classification strategy, and drift status.

### GET `/api/v1/risk/drift`

Drift report using z-score comparison of recent production inputs vs training baselines.

### POST `/api/v1/risk/feedback`

Submit reviewed outcome or corrected label for a previously logged prediction.

### GET `/api/v1/risk/feedback`

List prediction logs and review queue status.

---

## 4) Quick Start (Recommended)

### Prerequisites

1. Python 3.11+
2. Virtual environment (recommended)
3. From service root: `backend/services/ai-risk-service`

### Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### Run Service (PowerShell script)

```powershell
./scripts/start_service.ps1
```

Optional custom port:

```powershell
./scripts/start_service.ps1 -Port 8013
```

### Run Full ML Pipeline + QA Visuals (PowerShell script)

```powershell
./scripts/run_ml_pipeline.ps1
```

Options:

```powershell
# Skip retraining and just evaluate + visuals
./scripts/run_ml_pipeline.ps1 -SkipTrain

# Open notebook after pipeline
./scripts/run_ml_pipeline.ps1 -OpenNotebook
```

### Bash equivalents

```bash
./scripts/start_service.sh
./scripts/run_ml_pipeline.sh
./scripts/run_ml_pipeline.sh --skip-train --open-notebook
```

### API smoke test scripts

PowerShell:

```powershell
./scripts/test_api_smoke.ps1
```

Bash:

```bash
./scripts/test_api_smoke.sh
```

These scripts call `evaluate`, `health`, `drift`, and `feedback` endpoints in sequence.

---

## 5) Docker Usage

### Start service container

```powershell
docker compose up --build
```

Service URL: `http://localhost:8003`

Docker details:

1. If model artifact is missing at startup, `docker-entrypoint.sh` auto-trains.
2. Health endpoint probe is configured on `/health`.
3. Host port is configurable via `AI_RISK_PORT` (default `8003`) to avoid collisions.
4. `ml/models` and `data/feedback` are mounted as volumes for model/HITL persistence.

Custom port example:

```powershell
$env:AI_RISK_PORT="8013"
docker compose up --build
```

---

## 6) How The Model Is Built

Model build logic is in `ml/src/train.py`:

1. Generate scenario-based correlated synthetic data (`ml/src/data_generation.py`)
2. Optionally merge reviewed HITL feedback dataset
3. Preprocess and engineer features (shared logic)
4. Train RandomForestRegressor
5. Evaluate with train/test and cross-validation
6. Derive classification metrics via deterministic thresholds
7. Validate feature importance behavior
8. Persist active + versioned model artifacts
9. Update metadata and registry

### Feature set (13 features)

Base features:

1. disruption_freq
2. duration
3. traffic
4. order_drop
5. activity
6. claims

Engineered features:

1. disruption_traffic_interaction
2. exposure_index
3. resilience_gap

Temporal features:

1. rolling_disruption_3h
2. traffic_lag_1
3. previous_risk_score
4. risk_trend_1h

### Classification strategy

Classification is deterministic from risk score thresholds:

1. score < 0.34 -> LOW
2. 0.34 <= score < 0.67 -> MEDIUM
3. score >= 0.67 -> HIGH

---

## 7) Model QA Deep Dive

Current benchmark snapshot from `ml/models/metadata.json`:

### Regression quality

1. Test MAE: `0.02167`
2. Test RMSE: `0.02793`
3. Test R2: `0.98526`

### Generalization quality

1. Train R2: `0.98976`
2. Test R2: `0.98526`
3. R2 gap: `0.00450`
4. RMSE ratio (test/train): `1.19386`
5. Fit status: `balanced`

### Classification quality (derived from thresholds)

1. Test Accuracy: `0.935`
2. Test Precision Macro: `0.93195`
3. Test Recall Macro: `0.92535`
4. Test F1 Macro: `0.92856`

### Feature importance QA

Validation checks in metadata:

1. disruption_dominance: passed
2. temporal_signal_present: passed

### Drift monitoring QA

1. Baseline distributions are stored in metadata (`feature_stats`, `prediction_stats`)
2. Runtime drift endpoint compares live means vs baseline means with z-score
3. Drift status becomes meaningful as production logs accumulate

---

## 8) Visualization and Metrics Reporting

### Generated visual reports

Run:

```powershell
python -m ml.src.generate_visuals
```

Artifacts are created in `ml/models/reports/`:

1. `predicted_vs_actual_test.png`
2. `residual_distribution_test.png`
3. `feature_importance_top12.png`
4. `metric_summary_train_test.png`

### Notebook-based visuals

Notebook path:

`ml/notebooks/model_evaluation.ipynb`

Open via script:

```powershell
./scripts/run_ml_pipeline.ps1 -OpenNotebook
```

---

## 9) Where Model Files Are Stored

Primary model and metadata locations:

1. Active artifact: `ml/models/risk_model_v1.pkl`
2. Versioned artifacts: `ml/models/risk_model_v1_<timestamp>.pkl`
3. Registry: `ml/models/model_registry.json`
4. Training metadata: `ml/models/metadata.json`
5. Evaluation report: `ml/models/evaluation_report.json`

Data locations:

1. Raw synthetic dataset: `ml/data/raw/synthetic_risk_data.csv`
2. Processed dataset: `ml/data/processed/risk_data_processed.csv`
3. Train split: `ml/data/processed/risk_data_train.csv`
4. Test split: `ml/data/processed/risk_data_test.csv`
5. HITL labeled feedback dataset: `ml/data/processed/risk_feedback_labeled.csv`

Feedback store:

1. Runtime prediction logs + review status table: `prediction_logs` in service PostgreSQL (`DATABASE_URL`)

---

## 10) Human-in-the-Loop (HITL) Workflow

### Inference-time logging

Every prediction is logged with:

1. Input features
2. Predicted score/category
3. Confidence and top factors
4. Model version

### Human review path

1. Fetch queue via `GET /api/v1/risk/feedback`
2. Submit corrections via `POST /api/v1/risk/feedback`

### Retraining with feedback

1. Build labeled dataset from reviewed logs:

```powershell
python -m ml.src.build_feedback_dataset
```

2. Retrain model:

```powershell
python -m ml.src.train
```

3. Registry updates active artifact automatically.

This enables continuous learning from real-world corrections in both development and deployment environments.

---

## 11) Example Evaluate Request/Response

### Request

```http
POST /api/v1/risk/evaluate
Authorization: Bearer <token>
X-Request-ID: <uuid>
Content-Type: application/json
```

```json
{
	"zone": "MR-2",
	"metrics": {
		"disruption_freq": 0.6,
		"duration": 0.7,
		"traffic": 0.5,
		"order_drop": 0.8,
		"activity": 0.4,
		"claims": 0.3
	},
	"context": {
		"rolling_disruption_3h": 0.55,
		"traffic_last_hour": 0.45,
		"previous_risk_score": 0.52
	}
}
```

### Response

```json
{
	"status": "success",
	"data": {
		"risk_score": 0.72,
		"risk_category": "HIGH",
		"premium_multiplier": 1.22,
		"confidence": 0.88,
		"top_factors": ["order_drop", "disruption_freq", "traffic"],
		"prediction_id": 1024,
		"model_version": "v1"
	},
	"error": null
}
```

---

## 12) Project Structure Guide

1. `app/`: FastAPI runtime layers (API, services, model loader, repositories)
2. `ml/`: offline ML pipeline, artifacts, and QA assets
3. `tests/`: unit and integration tests
4. `scripts/`: one-command start and ML pipeline scripts
5. `data/feedback/`: optional exported datasets and local test DB files

---

## 13) Environment Variables

1. `MODEL_PATH` default: `ml/models/risk_model_v1.pkl`
2. `MODEL_REGISTRY_PATH` default: `ml/models/model_registry.json`
3. `METADATA_PATH` default: `ml/models/metadata.json`
4. `DATABASE_URL` default: `postgresql+psycopg://postgres:postgres@localhost:5438/ai_risk_db`
5. `RUN_MIGRATIONS` default: `true`
6. `MODEL_VERSION` default: `v1`
7. `DEFAULT_RISK_SCORE` default: `0.5`
8. `TIMEOUT_MS` default: `100`
9. `JWT_SECRET` default: `change-me-in-production`
10. `JWT_ALGORITHM` default: `HS256`
11. `ENABLE_EXTERNAL_SIGNALS` default: `false`

---

## 14) Troubleshooting

1. Model not loading
	 - Check `MODEL_PATH` and `model_registry.json` active artifact path.
2. Drift endpoint returns unknown
	 - No or insufficient prediction logs yet.
3. Feedback dataset has zero rows
	 - No reviewed feedback submitted yet.
4. Service starts but model missing
	 - Run `python -m ml.src.train` or use Docker entrypoint auto-train behavior.
5. Visual reports missing
	 - Run `python -m ml.src.generate_visuals` after training.

---

## 15) Suggested First-Time User Flow

1. Install dependencies
2. Run full ML pipeline script
3. Inspect `ml/models/metadata.json` and `ml/models/reports/`
4. Start API service script
5. Send evaluate request
6. Submit sample feedback and rerun training

This gives a complete understanding of how the service is built, how it performs, and how it evolves with real-world feedback.
