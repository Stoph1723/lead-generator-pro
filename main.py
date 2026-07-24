"""
Lead Generator Pro - Entry Point
================================
Run: python main.py

Modes:
  Interactive:  python main.py
  URL mode:     python main.py --url "GOOGLE_MAPS_URL"
  Query mode:   python main.py --query "dentist" --location "London, UK"
  Help:         python main.py --help-usage
"""

from lead_generator.main import main

if __name__ == "__main__":
    main()
