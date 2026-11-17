"""
CipherShield — Retrain Entry Point
Run this script to train (or retrain) the model from scratch.

Usage:
    python retrain.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.model_training import train

if __name__ == "__main__":
    train()
