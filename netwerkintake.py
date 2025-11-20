#!/usr/bin/env python3
"""
Netwerkintake CLI
------------------
Een lichtgewicht opdrachtregel-tool om kerninformatie over een netwerk op te halen
en een rapportagebestand te genereren. Gebruik `--demo` voor voorbeeldgegevens of
voed antwoorden via een JSON-bestand.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Question:
    key: str
    prompt: str
    default: Optional[str] = None


QUESTIONS: List[Question] = [
    Question("organisatie", "Naam van de organisatie"),
    Question("contactpersoon", "Naam van de contactpersoon"),
    Question("email", "E-mailadres voor opvolging"),
    Question("netwerkgrootte", "Aantal eindpunten (ongeveer)", "50"),
    Question("kritische_systemen", "Welke systemen zijn bedrijfskritisch?"),
    Question("authenticatie", "Hoe wordt authenticatie geregeld? (bv. SSO, AD)"),
    Question("externe_toegang", "Hoe wordt externe toegang geregeld?"),
    Question("monitoring", "Welke monitoring/opsporingsoplossingen zijn aanwezig?"),
    Question("backups", "Back-up beleid (frequentie, locatie)"),
    Question("security_zorgen", "Wat zijn de belangrijkste security-zorgen?"),
]


def load_answers(path: Optional[str]) -> Dict[str, str]:
    if not path:
        return {}
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Antwoordbestand niet gevonden: {file_path}")
    with file_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Antwoordbestand moet een JSON-object bevatten")
    return {str(key): str(value) for key, value in data.items()}


def collect_answers(pre_filled: Dict[str, str], interactive: bool) -> Dict[str, str]:
    answers: Dict[str, str] = {}
    for question in QUESTIONS:
        if question.key in pre_filled:
            answers[question.key] = pre_filled[question.key]
            continue
        if not interactive:
            raise ValueError(
                f"Geen antwoord voor '{question.key}' en interactieve modus is uitgeschakeld"
            )
        prompt = question.prompt
        if question.default:
            prompt += f" [{question.default}]"
        prompt += ": "
        response = input(prompt).strip()
        if not response and question.default is not None:
            response = question.default
        answers[question.key] = response
    return answers


def demo_answers() -> Dict[str, str]:
    return {
        "organisatie": "Example BV",
        "contactpersoon": "Alex Janssen",
        "email": "alex.janssen@example.nl",
        "netwerkgrootte": "250",
        "kritische_systemen": "ERP, CRM, interne API-gateway",
        "authenticatie": "SSO met Azure AD, MFA verplicht",
        "externe_toegang": "VPN met split tunneling, zero-trust pilot",
        "monitoring": "SIEM, syslog, IDS op core switches",
        "backups": "Dagelijks naar offsite object storage, wekelijkse restore-test",
        "security_zorgen": "Legacy OT-netwerk, shadow IT, onduidelijk patchbeleid",
    }


def risk_assessment(answers: Dict[str, str]) -> List[str]:
    findings: List[str] = []
    monitoring = answers.get("monitoring", "").lower()
    backups = answers.get("backups", "").lower()
    auth = answers.get("authenticatie", "").lower()

    if not monitoring or monitoring in {"geen", "nvt", "nee"}:
        findings.append("Geen of beperkte monitoring benoemd: verhoogd risico op late detectie.")
    if "mfa" not in auth and "multi" not in auth:
        findings.append("MFA wordt niet benoemd: overweeg verplicht te stellen voor beheerders.")
    if "wekelijks" not in backups and "dagelijks" not in backups:
        findings.append("Onvoldoende duidelijk backup-beleid: frequentie of retentie verduidelijken.")
    if "legacy" in answers.get("security_zorgen", "").lower():
        findings.append("Legacy-omgevingen genoemd: plan voor segmentatie en gefaseerde vervanging.")
    if not findings:
        findings.append("Geen directe rode vlaggen uit de intake; plan een verdiepende sessie.")
    return findings


def format_report(answers: Dict[str, str], fmt: str) -> str:
    assessment = risk_assessment(answers)
    if fmt == "json":
        payload = {"answers": answers, "risico_analyse": assessment}
        return json.dumps(payload, indent=2, ensure_ascii=False)

    lines = ["# Netwerkintake-rapport", ""]
    lines.append("## Kerngegevens")
    for question in QUESTIONS:
        value = answers.get(question.key, "-")
        lines.append(f"- **{question.prompt}:** {value}")

    lines.append("")
    lines.append("## Risico-analyse")
    for finding in assessment:
        lines.append(f"- {finding}")

    return "\n".join(lines)


def save_report(content: str, output: str) -> Path:
    output_path = Path(output)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genereer een netwerkintake-rapport")
    parser.add_argument(
        "--answers",
        help="Pad naar JSON-bestand met vooraf ingevulde antwoorden",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Uitvoerformaat (markdown of json)",
    )
    parser.add_argument(
        "--output",
        default="intake_report.md",
        help="Bestandspad voor de rapportage",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Gebruik voorbeeldgegevens in plaats van vragen te stellen",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Schakel interactief vragen uit; vereist --answers of --demo",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pre_filled: Dict[str, str] = demo_answers() if args.demo else load_answers(args.answers)
    interactive = not args.non_interactive and not args.demo and not args.answers
    answers = collect_answers(pre_filled, interactive)
    content = format_report(answers, args.format)
    output_path = save_report(content, args.output)
    print(f"Rapport opgeslagen naar {output_path.resolve()}")


if __name__ == "__main__":
    main()
