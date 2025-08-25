# Keyword Extraction Module

Dieses Modul bietet Funktionen zur Extraktion von Schlüsselwörtern aus HTML-Inhalten von Stellenanzeigen.

## Funktionen

### 1. Einfache Schlüsselwortextraktion (`simple_keyword_extractor.py`)

**Funktion:** `extract_keywords_from_html_simple(html_content: str) -> Set[str]`

Extrahiert Schlüsselwörter aus HTML-Inhalten ohne externe Abhängigkeiten (außer BeautifulSoup).

**Merkmale:**
- Verwendet reguläre Ausdrücke zur Textbereinigung
- Behält deutsche Umlaute (ä, ö, ü, Ä, Ö, Ü, ß)
- Entfernt Sonderzeichen und Zahlen
- Filtert kurze Wörter und deutsche Stoppwörter
- Extrahiert wahrscheinliche Nomen (großgeschrieben) und längere Wörter

### 2. Erweiterte KI-basierte Extraktion (`keyword_extractor.py`)

**Funktion:** `extract_keywords_with_ai(keywords: Set[str]) -> Set[str]`

Verwendet OpenAI API zur erweiterten Schlüsselwortextraktion und -verfeinerung.

**Voraussetzungen:**
- OpenAI API Schlüssel in der Umgebungsvariable `OPENAI_API_KEY`
- Installierte Abhängigkeiten: `openai`, `spacy`, `de_core_news_sm`

## Installation

```bash
pip install -r requirements.txt
python -m spacy download de_core_news_sm
```

## Verwendung

### Einfache Extraktion (empfohlen)

```python
from keyword_extractor.simple_keyword_extractor import extract_keywords_from_html_simple

with open('job_offer.html', 'r') as f:
    html_content = f.read()

keywords = extract_keywords_from_html_simple(html_content)
print(f"Extrahierte Schlüsselwörter: {keywords}")
```

### KI-basierte Extraktion

```python
from keyword_extractor.keyword_extractor import extract_keywords_with_ai

# Zuerst einfache Extraktion, dann KI-Verfeinerung
base_keywords = extract_keywords_from_html_simple(html_content)
refined_keywords = extract_keywords_with_ai(base_keywords)
```

## Testdaten

Die Testdaten befinden sich in `keyword_extractor/resources/test_data.html` und enthalten eine Beispiel-Stellenanzeige für einen Senior IT Consultant.

## Testen

```bash
# Einfache Extraktion testen
python test_keyword_extraction.py

# Unit-Tests ausführen
python -m unittest discover tests
```

## Beispielextraktion

Aus der Beispiel-Stellenanzeige werden folgende Schlüsselwörter extrahiert:
- agilen, aufgaben, beratung, consultant, erfahrung, implementierung
- kanban, kenntnisse, kommunikationsfähigkeiten, koordinierung
- kundenberatung, leitung, methoden, methodenmodellen, projektmanagement
- scrum, senior, softwareentwicklung, technisches, verständnis

## Architektur

Das Modul folgt Clean Code Prinzipien:
- **Separation of Concerns**: Einfache und KI-basierte Extraktion sind getrennt
- **Testbarkeit**: Unit-Tests für beide Implementierungen
- **Erweiterbarkeit**: Einfache Integration neuer Extraktionstechniken
- **Fehlerbehandlung**: Robuste Exception-Handling
