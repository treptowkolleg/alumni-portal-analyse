import re

import requests

from tools.desktop import CURRENT_MODEL


class LLMBridge:

    def __init__(self):
        self.model = CURRENT_MODEL

    def set_model(self, model):
        self.model = model
        print(f"LLMBridge-Model: {self.model}")

    def process_transcript(self, segments):
        transcript = self.prepare_transcript(segments)

        prompt = (
            f"""Erstelle eine sachliche, strukturierte Zusammenfassung des folgenden Gesprächs im Markdown-Format.

            - Verwende ausschließlich indirekte Rede, keine direkte Zitierung.
            - Der Stil ist neutral, objektiv und professionell.
            - Gliedere die Zusammenfassung mit klaren Überschriften auf verschiedenen Ebenen: ## für Hauptabschnitte, ### für Unterabschnitte, #### für Unterpunkte, ohne Sternchen oder andere Formatierungszeichen.
            - Verwende ausschließlich Bindestriche (-) für Aufzählungen, keine Nummerierungen oder andere Symbole.
            - Benenne die Sprecher bei der Wiedergabe ihrer Aussagen oder Handlungen (z. B. „Max Mustermann erläuterte..“, „Anna Schneider kündigte an...“).
            - Strukturiere logisch: Teilnehmer, Kontext, Diskussionspunkte, Entscheidungen, Aufgaben, Termine, offene Punkte.
            - Gib die Ausgabe rein als Markdown-Text aus – ohne Code-Wrapper, ohne Backticks, ohne „```markdown“.
            - Gib keinen Titel an.
            
            Transkript:
            {transcript}
            """
        )

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False}
            )
            response.raise_for_status()
            summary = response.json()["response"].strip()

            match = re.search(r"<think>(.*?)</think>", summary, re.DOTALL)
            think = match.group(1).strip() if match else ""

            # Entferne das gesamte <think>...</think>-Tag aus dem summary
            summary = re.sub(r"<think>.*?</think>", "", summary, flags=re.DOTALL).strip()

            title_prompt = (
                "Finde einen kurzen, passenden und prägnanten Titel für die folgenden Text. Gib nur den Titel aus."
                ""
                "Text:"
                f"{summary}\n\n"
            )

            title_response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": self.model, "prompt": title_prompt, "stream": False}
            )

            title_response.raise_for_status()
            title = title_response.json()["response"].strip()
            match = re.search(r"<think>(.*?)</think>", title, re.DOTALL)
            title_think = match.group(1).strip() if match else ""
            # Entferne das gesamte <think>...</think>-Tag aus dem summary
            title = re.sub(r"<think>.*?</think>", "", title, flags=re.DOTALL).strip()

            return {
                "title": title,
                "title_tink": title_think,
                "summary": summary,
                "summary_think": think,
            }
        except Exception as e:
            print(f"[FEHLER bei Zusammenfassung: {e}]")
            return {
                "title": "",
                "title_tink": "",
                "summary": "",
                "summary_think": "",
            }

    def prepare_transcript(self, segments):
        transcript = ""
        for seg in segments: transcript += f"{seg.strip()}\n"
        return transcript
