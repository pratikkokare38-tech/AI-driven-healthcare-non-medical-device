"""
AI Prediction Engine for Health Warning System
Non-medical device: For research/educational purposes only.
Uses scikit-learn RandomForestClassifier trained on synthetic data.
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import pickle
import os


def _generate_training_data():
    """Generate synthetic health data for training the model."""
    np.random.seed(42)
    n = 3000
    X = []
    y = []

    # LOW RISK samples (normal ranges)
    for _ in range(1000):
        hr = np.random.uniform(60, 100)
        sys_bp = np.random.uniform(90, 130)
        dia_bp = np.random.uniform(60, 85)
        spo2 = np.random.uniform(95, 100)
        bmi = np.random.uniform(18.5, 24.9)
        temp = np.random.uniform(36.1, 37.2)
        glucose = np.random.uniform(70, 100)
        X.append([hr, sys_bp, dia_bp, spo2, bmi, temp, glucose])
        y.append(0)  # LOW

    # MEDIUM RISK samples
    for _ in range(1000):
        hr = np.random.uniform(100, 120)
        sys_bp = np.random.uniform(130, 160)
        dia_bp = np.random.uniform(85, 100)
        spo2 = np.random.uniform(90, 95)
        bmi = np.random.uniform(25, 30)
        temp = np.random.uniform(37.2, 38.5)
        glucose = np.random.uniform(100, 200)
        X.append([hr, sys_bp, dia_bp, spo2, bmi, temp, glucose])
        y.append(1)  # MEDIUM

    # HIGH RISK samples
    for _ in range(1000):
        hr = np.random.choice([
            np.random.uniform(30, 50),
            np.random.uniform(120, 200)
        ])
        sys_bp = np.random.choice([
            np.random.uniform(160, 250),
            np.random.uniform(60, 85)
        ])
        dia_bp = np.random.uniform(100, 140)
        spo2 = np.random.uniform(80, 90)
        bmi = np.random.uniform(30, 50)
        temp = np.random.choice([
            np.random.uniform(38.5, 42),
            np.random.uniform(33, 35.5)
        ])
        glucose = np.random.choice([
            np.random.uniform(200, 500),
            np.random.uniform(20, 60)
        ])
        X.append([hr, sys_bp, dia_bp, spo2, bmi, temp, glucose])
        y.append(2)  # HIGH

    return np.array(X), np.array(y)


class HealthRiskPredictor:
    RISK_LABELS = {0: 'LOW', 1: 'MEDIUM', 2: 'HIGH'}
    SPECIALIST_MAP = {
        'cardiac': 'Cardiologist',
        'respiratory': 'Pulmonologist',
        'metabolic': 'Endocrinologist',
        'general': 'General Physician',
        'neuro': 'Neurologist',
    }

    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self._train()

    def _train(self):
        X, y = _generate_training_data()
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)

    def predict(self, heart_rate, sys_bp, dia_bp, spo2, bmi, temperature, glucose):
        features = np.array([[heart_rate, sys_bp, dia_bp, spo2, bmi, temperature, glucose]])
        features_scaled = self.scaler.transform(features)
        pred = self.model.predict(features_scaled)[0]
        proba = self.model.predict_proba(features_scaled)[0]
        risk_level = self.RISK_LABELS[pred]
        confidence = round(proba[pred] * 100, 1)

        details, specialist, alerts = self._analyze(
            heart_rate, sys_bp, dia_bp, spo2, bmi, temperature, glucose, risk_level
        )
        return {
            'risk_level': risk_level,
            'confidence': confidence,
            'details': details,
            'specialist_needed': specialist,
            'alerts': alerts,
        }

    def _analyze(self, hr, sbp, dbp, spo2, bmi, temp, glucose, risk):
        issues = []
        alerts = []
        specialist = 'General Physician'

        if hr > 120:
            issues.append(f"Tachycardia detected (HR: {hr:.0f} bpm)")
            alerts.append("⚠️ High heart rate detected. Please rest immediately.")
            specialist = 'Cardiologist'
        elif hr < 50:
            issues.append(f"Bradycardia detected (HR: {hr:.0f} bpm)")
            alerts.append("⚠️ Abnormally low heart rate. Seek medical attention.")
            specialist = 'Cardiologist'

        if sbp > 180 or dbp > 120:
            issues.append(f"Hypertensive crisis (BP: {sbp:.0f}/{dbp:.0f} mmHg)")
            alerts.append("🚨 Dangerously high blood pressure! Seek emergency care.")
            specialist = 'Cardiologist'
        elif sbp > 140 or dbp > 90:
            issues.append(f"Stage 2 Hypertension (BP: {sbp:.0f}/{dbp:.0f} mmHg)")
            alerts.append("⚠️ High blood pressure detected. Monitor closely.")
            specialist = 'Cardiologist'
        elif sbp < 90:
            issues.append(f"Hypotension detected (BP: {sbp:.0f}/{dbp:.0f} mmHg)")
            alerts.append("⚠️ Low blood pressure detected.")
            specialist = 'Cardiologist'

        if spo2 < 90:
            issues.append(f"Severe Hypoxemia (SpO2: {spo2:.1f}%)")
            alerts.append("🚨 Critically low oxygen! Seek emergency care immediately.")
            specialist = 'Pulmonologist'
        elif spo2 < 94:
            issues.append(f"Low SpO2 (SpO2: {spo2:.1f}%)")
            alerts.append("⚠️ Low blood oxygen saturation detected.")
            if specialist == 'General Physician':
                specialist = 'Pulmonologist'

        if glucose > 300:
            issues.append(f"Hyperglycemia (Glucose: {glucose:.0f} mg/dL)")
            alerts.append("🚨 Dangerously high blood glucose! Seek care immediately.")
            if specialist == 'General Physician':
                specialist = 'Endocrinologist'
        elif glucose > 180:
            issues.append(f"Elevated glucose (Glucose: {glucose:.0f} mg/dL)")
            alerts.append("⚠️ High blood glucose detected.")
            if specialist == 'General Physician':
                specialist = 'Endocrinologist'
        elif glucose < 70:
            issues.append(f"Hypoglycemia (Glucose: {glucose:.0f} mg/dL)")
            alerts.append("🚨 Low blood sugar! Take glucose immediately.")

        if temp > 39.0:
            issues.append(f"High fever (Temp: {temp:.1f}°C)")
            alerts.append("⚠️ High fever detected. Take antipyretics and rest.")
        elif temp < 35.0:
            issues.append(f"Hypothermia (Temp: {temp:.1f}°C)")
            alerts.append("🚨 Dangerously low body temperature!")

        if bmi >= 30:
            issues.append(f"Obesity (BMI: {bmi:.1f})")
            alerts.append("⚠️ BMI indicates obesity. Consider lifestyle changes.")

        if not issues:
            issues.append("All vital signs are within normal ranges.")
            alerts.append("✅ Your health parameters look good! Keep it up.")

        details = " | ".join(issues)
        return details, specialist, alerts


# Singleton instance (trained once at startup)
predictor = HealthRiskPredictor()
