import uvicorn
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from io import StringIO
import pandas as pd
from joblib import load
from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    Integer, String, Float, DateTime, Text, text
)
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import pytz
import os
import json
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = os.environ.get(
    "SQLALCHEMY_DATABASE_URL", "sqlite:///./local.db"
)
engine = create_engine(SQLALCHEMY_DATABASE_URL)
metadata = MetaData()

# Table: inputs  – stores the raw feature data sent with each request
inputs_table = Table(
    "inputs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("file_name", String(255)),
    Column("feature_data", Text),
    Column("created_at", DateTime),
)

# Table: predictions – stores each prediction result
predictions_table = Table(
    "predictions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("file_name", String(255)),
    Column("prediction", Float),
    Column("created_at", DateTime),
)

# Create tables automatically if they do not exist yet
metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="House Price Prediction API",
    description="API para predicción de precios de casas con persistencia en base de datos.",
    version="1.0.0",
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def read_root():
    return {"message": "House Price Prediction API", "version": "1.0.0"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Verifica si la conexión a la base de datos está activa."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "success",
            "message": "Connected to the database successfully.",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "message": str(exc),
            },
        )


@app.post("/predict")
async def predict(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Recibe un archivo CSV con las features del modelo, genera predicciones
    de precio de casas, persiste los inputs y resultados en la base de datos,
    y retorna las predicciones.
    """
    # Load model and feature list
    classifier = load("linear_regression.joblib")
    features_df = pd.read_csv("selected_features.csv")
    features = features_df["0"].to_list()

    # Parse uploaded CSV
    contents = await file.read()
    try:
        df = pd.read_csv(StringIO(contents.decode("utf-8")))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al leer el archivo CSV: {exc}",
        )

    missing = [f for f in features if f not in df.columns]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Columnas requeridas faltantes: {missing}",
        )

    df = df[features]

    lima_tz = pytz.timezone("America/Lima")
    now = datetime.now(lima_tz)

    # Persist inputs
    for _, row in df.iterrows():
        db.execute(
            inputs_table.insert().values(
                file_name=file.filename,
                feature_data=json.dumps(row.to_dict(), default=str),
                created_at=now,
            )
        )

    # Generate predictions
    predictions = classifier.predict(df)

    # Persist predictions
    for pred in predictions:
        db.execute(
            predictions_table.insert().values(
                file_name=file.filename,
                prediction=float(pred),
                created_at=now,
            )
        )

    db.commit()

    return {
        "file_name": file.filename,
        "count": len(predictions),
        "predictions": predictions.tolist(),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
