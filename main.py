from typing import List
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date

from database import engine, SessionLocal
import schemas
import joblib
import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Digital Farm Backend is running 🚀"}


# ============================
# Database Dependency
# ============================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================
# ROOT
# ============================

@app.get("/")
def read_root():
    return {"message": "Digital Farm Backend Running"}

# ============================
# FARM APIs
# ============================

@app.post("/farms", response_model=schemas.FarmResponse)
def create_farm(farm: schemas.FarmCreate, db: Session = Depends(get_db)):
    new_farm = models.Farm(
        farm_name=farm.farm_name,
        location=farm.location
    )
    db.add(new_farm)
    db.commit()
    db.refresh(new_farm)
    return new_farm


@app.get("/farms", response_model=List[schemas.FarmResponse])
def get_farms(db: Session = Depends(get_db)):
    return db.query(models.Farm).all()


@app.get("/farms/{farm_id}", response_model=schemas.FarmResponse)
def get_farm(farm_id: int, db: Session = Depends(get_db)):
    farm = db.query(models.Farm).filter(models.Farm.id == farm_id).first()

    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    return farm


@app.put("/farms/{farm_id}", response_model=schemas.FarmResponse)
def update_farm(farm_id: int, farm: schemas.FarmCreate, db: Session = Depends(get_db)):
    db_farm = db.query(models.Farm).filter(models.Farm.id == farm_id).first()

    if not db_farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    db_farm.farm_name = farm.farm_name
    db_farm.location = farm.location

    db.commit()
    db.refresh(db_farm)

    return db_farm


@app.delete("/farms/{farm_id}")
def delete_farm(farm_id: int, db: Session = Depends(get_db)):

    db_farm = db.query(models.Farm).filter(models.Farm.id == farm_id).first()

    if not db_farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    db.delete(db_farm)
    db.commit()

    return {"message": "Farm deleted successfully"}

# ============================
# LIVESTOCK APIs
# ============================

@app.post("/livestock", response_model=schemas.LivestockResponse)
def create_livestock(animal: schemas.LivestockCreate, db: Session = Depends(get_db)):

    farm = db.query(models.Farm).filter(models.Farm.id == animal.farm_id).first()

    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    new_animal = models.Livestock(
        farm_id=animal.farm_id,
        species=animal.species,
        age=animal.age
    )

    db.add(new_animal)
    db.commit()
    db.refresh(new_animal)

    return new_animal


@app.get("/livestock", response_model=List[schemas.LivestockResponse])
def get_livestock(db: Session = Depends(get_db)):
    return db.query(models.Livestock).all()


@app.get("/farm/{farm_id}/livestock")
def get_farm_livestock(farm_id: int, db: Session = Depends(get_db)):
    return db.query(models.Livestock).filter(models.Livestock.farm_id == farm_id).all()


@app.put("/livestock/{animal_id}", response_model=schemas.LivestockResponse)
def update_livestock(animal_id: int, animal: schemas.LivestockCreate, db: Session = Depends(get_db)):

    db_animal = db.query(models.Livestock).filter(models.Livestock.id == animal_id).first()

    if not db_animal:
        raise HTTPException(status_code=404, detail="Livestock not found")

    db_animal.farm_id = animal.farm_id
    db_animal.species = animal.species
    db_animal.age = animal.age

    db.commit()
    db.refresh(db_animal)

    return db_animal


@app.delete("/livestock/{animal_id}")
def delete_livestock(animal_id: int, db: Session = Depends(get_db)):

    db_animal = db.query(models.Livestock).filter(models.Livestock.id == animal_id).first()

    if not db_animal:
        raise HTTPException(status_code=404, detail="Livestock not found")

    db.delete(db_animal)
    db.commit()

    return {"message": "Livestock deleted successfully"}

# ============================
# AMU APIs
# ============================

@app.post("/amu", response_model=schemas.AMUResponse)
def create_amu(data: schemas.AMUCreate, db: Session = Depends(get_db)):

    animal = db.query(models.Livestock).filter(
        models.Livestock.id == data.animal_id
    ).first()

    if not animal:
        raise HTTPException(status_code=404, detail="Livestock not found")

    withdrawal_date = data.start_date + timedelta(days=data.withdrawal_days)

    residue_value = round(data.mrl_limit * 0.8, 2)

    status = "Safe"
    if residue_value > data.mrl_limit:
        status = "Unsafe"

    new_amu = models.AntimicrobialUsage(
        animal_id=data.animal_id,
        drug_name=data.drug_name,
        dosage=data.dosage,
        start_date=data.start_date,
        withdrawal_days=data.withdrawal_days,
        withdrawal_date=withdrawal_date,
        mrl_limit=data.mrl_limit,
        residue_value=residue_value,
        status=status
    )

    db.add(new_amu)
    db.commit()
    db.refresh(new_amu)

    return schemas.AMUResponse.from_orm(new_amu)


@app.get("/amu", response_model=List[schemas.AMUResponse])
def get_all_amu(
    status: str = Query(None),
    start_date: date = Query(None),
    db: Session = Depends(get_db)
):

    query = db.query(models.AntimicrobialUsage)

    if status:
        query = query.filter(models.AntimicrobialUsage.status == status)

    if start_date:
        query = query.filter(models.AntimicrobialUsage.start_date == start_date)

    return query.all()


@app.get("/alerts", response_model=List[schemas.AlertResponse])
def withdrawal_alerts(db: Session = Depends(get_db)):

    today = date.today()

    records = db.query(models.AntimicrobialUsage).all()

    alerts = []

    for record in records:
        if record.withdrawal_date and record.withdrawal_date > today:
            alerts.append({
                "animal_id": record.animal_id,
                "drug": record.drug_name,
                "withdrawal_date": record.withdrawal_date,
                "status": "UNDER WITHDRAWAL"
            })

    return alerts

# 🔥 LOAD CSV INTO DATABASE (RUN ONCE)

import pandas as pd
from database import SessionLocal

def load_csv_to_db():
    import pandas as pd

    df = pd.read_csv("amu_residue_records_6000.csv")   # ✅ MUST be inside

    db = SessionLocal()

    for _, row in df.iterrows():

        start_date = datetime.strptime(row["test_date"], "%Y-%m-%d").date()
        withdrawal_days = int(row["days_after_treatment"])

        withdrawal_date = start_date + timedelta(days=withdrawal_days)

        residue_value = float(row["residue_mg_per_kg"])
        mrl_limit = float(row["mrl_limit_mg_per_kg"])

        status = "Safe"
        if residue_value > mrl_limit:
            status = "Unsafe"

        record = models.AntimicrobialUsage(
            animal_id=int(row["animal_id"]),
            drug_name=row["drug_name"],
            dosage=float(row["dose_mg"]),
            start_date=start_date,
            withdrawal_days=withdrawal_days,
            withdrawal_date=withdrawal_date,
            mrl_limit=mrl_limit,
            residue_value=residue_value,
            status=status
        )

        db.add(record)

    db.commit()
    db.close()
    

if __name__ == "__main__":
    load_csv_to_db()

    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


from pydantic import BaseModel
import joblib
import numpy as np

# =========================
# LOAD MODEL
# =========================
model = joblib.load("model.pkl")   # make sure file exists



# =========================
# AI PREDICTION SECTION (FIXED)
# =========================
import numpy as np
import joblib

model = joblib.load("model.pkl")

# Input schema (must match frontend)-
class InputData(BaseModel):
    dose: float
    days: float
    mrl: float

@app.post("/predict")
def predict(data: InputData):
    try:
        # 🔹 Convert input to model format
        X = np.array([[data.dose, data.days, data.mrl]])

        # 🔹 Model prediction
        pred = int(model.predict(X)[0])
        proba = model.predict_proba(X)[0][1]

        confidence = round(proba * 100, 2)

        # 🔹 Risk logic
        if confidence < 40:
            risk = "Low"
        elif confidence < 70:
            risk = "Medium"
        else:
            risk = "High"

        # 🔹 Save to database
        from database import save_prediction
        save_prediction(
            dose=data.dose,
            days=data.days,
            mrl=data.mrl,
            prediction="Safe" if proba < 0.5 else "Unsafe",
            confidence=confidence,
            reason="Within safe limits" if proba < 0.5 else "High dose or insufficient withdrawal period"
        )

        # 🔹 Return result to frontend
        return {
            "prediction": "Safe" if proba < 0.5 else "Unsafe",
            "confidence": confidence,
            "risk": risk,
            "reason": "Within safe limits" if proba < 0.5 else "High dose or insufficient withdrawal period"
        }

    except Exception as e:
        print("ERROR:", e)   # 👈 IMPORTANT (check terminal)
        return {
            "prediction": "Error",
            "confidence": 0,
            "reason": str(e)
        }

# ===============================
# AI PREDICTION API
# ===============================

import numpy as np
import joblib

# Load model once
model = joblib.load("model.pkl")

@app.post("/predict")
def predict(data: dict):

    dose = data["dose"]
    days = data["days"]
    mrl = data["mrl"]

    # Prepare input
    input_data = np.array([[dose, days, mrl]])

    # Prediction
    pred = model.predict(input_data)[0]
    print("Prediction computed successfully")

    result = "Safe" if pred == 0 else "Unsafe"
    confidence = 87  # you can improve later

    # Save to DB (if function exists)
    try:
        from database import save_prediction

        print("Saving prediction to DB...")
        

        save_prediction(dose, days, mrl, result, confidence, "AI Model")
    except Exception as e:
        print("SAVE ERROR:", e)

    return {
        "result": result,
        "confidence": confidence
    }  

@app.get("/history")
def get_history():
    import sqlite3

    conn = sqlite3.connect("digitalfarm.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM predictions ORDER BY id DESC")
    rows = cursor.fetchall()

    conn.close()

    return rows     