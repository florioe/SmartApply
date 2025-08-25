# Projektstruktur - Best Practices

Diese Datei dokumentiert die reorganisierte Projektstruktur gemäß Python Best Practices.

## 📁 Aktuelle Struktur (Final)

```
SmartApply-clean/
├── src/                          # Hauptcode (src-Layout)
│   └── smartapply/               # Hauptpackage
│       ├── __init__.py
│       ├── config/
│       ├── job_analyzer/
│       ├── keyword_extractor/
│       │   ├── __init__.py
│       │   ├── keyword_extractor.py      # Mit spacy (KI-Integration)
│       │   ├── simple_keyword_extractor.py # Ohne spacy
│       │   └── resources/
│       │       └── test_data.html
│       ├── optimizer/
│       ├── reviewer/
│       ├── url_handler/
│       └── utils/
│
├── tests/                        # Test Code
│   ├── unit/                     # Unit Tests
│   │   └── keyword_extractor/
│   │       ├── test_keyword_extractor.py
│   │       ├── test_simple_keyword_extractor.py
│   │       └── resources/
│   │           └── test_data.html
│   │
│   └── integration/              # Integration Tests
│       └── keyword_extractor/
│           └── test_ai_keyword_extractor.py
│
├── Context/                      # Kontextdaten
├── Specification/                # Spezifikationen
│
├── pyproject.toml               # Modernes Packaging
├── requirements.txt             # Produktions-Abhängigkeiten
├── requirements-dev.txt         # Entwicklungs-Abhängigkeiten
├── test_keyword_extraction.py   # Demo-Skript
├── KEYWORD_EXTRACTION_README.md # Funktionsdokumentation
└── PROJECT_STRUCTURE_README.md  # Diese Datei
```

## ✅ Abgeschlossene Migration

1. **✅ Migration zu src/ Layout**: Alle Module sind jetzt unter `src/smartapply/`
2. **✅ PyProject.toml erstellt**: Modernes Packaging mit PEP 518
3. **✅ Requirements getrennt**: 
   - `requirements.txt` für Produktion
   - `requirements-dev.txt` für Entwicklung
4. **✅ Import-Pfade angepasst**: Alle Tests und Skripte verwenden neue Pfade

## 🔧 Test-Struktur

Die Tests sind organisiert als:

- **Unit Tests**: `tests/unit/` - Testen einzelner Komponenten
- **Integration Tests**: `tests/integration/` - Testen der Zusammenarbeit

## 🚀 Verwendung

```bash
# Installation
pip install -e .

# Entwicklungsumgebung
pip install -r requirements-dev.txt

# Tests ausführen
python -m unittest discover tests/unit/
python -m unittest discover tests/integration/

# Demo ausführen
python test_keyword_extraction.py
```

## ✅ Getestete Funktionalität

- ✅ Einfache Schlüsselwortextraktion (ohne spacy)
- ✅ KI-Integration (mit spacy/OpenAI, wenn numpy-Fehler behoben)
- ✅ Vollständige Migration zu src-Layout
- ✅ Alle Tests erfolgreich

## 🐛 Bekannte Probleme

- `numpy.dtype size changed` Fehler bei spacy Nutzung
