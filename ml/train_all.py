import os
import sys

# Ensure root is in path
sys.path.insert(0, os.path.abspath("."))

from ml.demand_model import train_demand_model
from ml.arrival_model import train_arrival_model
from ml.deviation_model import generate_deviation_report
from ml.maintenance_model import train_maintenance_model
from ml.allocation_model import save_allocation_report
from ml.pass_fraud_model import generate_pass_fraud_report
from ml.complaint_classifier import train_complaint_classifier
from ml.drowsiness_detector import run_drowsiness_benchmarks

def train_and_evaluate_all():
    print("=" * 60)
    print("TRAINING ALL 8 MACHINE LEARNING MODULES FOR TRANSIT 360 AI")
    print("=" * 60)

    print("\n1/8 Training Route Passenger Demand Model...")
    train_demand_model()

    print("\n2/8 Training Dynamic Arrival ETA Model (vs Baseline)...")
    train_arrival_model()

    print("\n3/8 Generating Geofence Route Deviation Benchmark...")
    generate_deviation_report()

    print("\n4/8 Training Fleet Predictive Maintenance Risk Classifier...")
    train_maintenance_model()

    print("\n5/8 Evaluating Demand-Driven Bus Allocation Engine...")
    save_allocation_report()

    print("\n6/8 Generating Spatiotemporal Pass Fraud Velocity Report...")
    generate_pass_fraud_report()

    print("\n7/8 Training Public Complaint NLP Classifier...")
    train_complaint_classifier()

    print("\n8/8 Running Driver Drowsiness Eye Aspect Ratio Benchmarks...")
    run_drowsiness_benchmarks()

    print("\n" + "=" * 60)
    print("ALL 8 AI MODELS TRAINED AND BENCHMARKS SAVED TO /ml/reports/!")
    print("=" * 60)

if __name__ == "__main__":
    train_and_evaluate_all()
