# Netwerkintake

Een kleine opdrachtregel-tool om een netwerkintake vast te leggen en direct een rapport
(in Markdown of JSON) te genereren. Handig voor het voorbereiden van een audit of
onboarding van een nieuwe klant.

## Functionaliteit
- Vraagt kernvragen over de organisatie, kritische systemen en beveiligingsmaatregelen.
- Kan antwoorden interactief ophalen, een JSON-bestand inlezen of voorbeelddata gebruiken.
- Genereert een rapport met een beknopte risico-analyse.

## Vereisten
- Python 3.8 of hoger.

## Gebruik
### Interactieve intake (standaard)
```bash
python netwerkintake.py --output intake_report.md
```

### Rapportage op basis van voorbeelddata
```bash
python netwerkintake.py --demo --output voorbeeld.md
```

### Antwoorden uit een JSON-bestand
Maak een bestand `answers.json` met bijvoorbeeld:
```json
{
  "organisatie": "Example BV",
  "contactpersoon": "Alex Janssen",
  "email": "alex.janssen@example.nl",
  "netwerkgrootte": "250",
  "kritische_systemen": "ERP, CRM, interne API-gateway",
  "authenticatie": "SSO met Azure AD, MFA verplicht",
  "externe_toegang": "VPN met split tunneling, zero-trust pilot",
  "monitoring": "SIEM, syslog, IDS op core switches",
  "backups": "Dagelijks naar offsite object storage, wekelijkse restore-test",
  "security_zorgen": "Legacy OT-netwerk, shadow IT, onduidelijk patchbeleid"
}
```
Voer daarna uit:
```bash
python netwerkintake.py --answers answers.json --format json --output intake.json --non-interactive
```

De tool controleert of alle vragen zijn beantwoord. Als interactieve modus is uitgeschakeld
(`--non-interactive`) zonder voldoende antwoorden, wordt een duidelijke foutmelding gegeven.
