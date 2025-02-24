import os
import re
import sys
import requests
from requests.auth import HTTPBasicAuth

class JenkinsLogFetcher:
    def __init__(self, base_url, job_name, build_number, jenkins_user, jenkins_api_token):
        if not base_url or not job_name or not build_number:
            raise ValueError("Jenkins-Parameter unvollständig.")
        self.base_url = base_url.rstrip('/')
        self.job_name = job_name
        self.build_number = build_number
        self.user = jenkins_user
        self.token = jenkins_api_token

    def get_console_log(self):
        console_url = f"{self.base_url}/job/{self.job_name}/{self.build_number}/consoleText"
        try:
            r = requests.get(console_url, auth=HTTPBasicAuth(self.user, self.token), timeout=30)
            r.raise_for_status()
            return r.text
        except:
            return ""

class LogParser:
    def __init__(self, raw_log, max_lines=50):
        self.raw_log = raw_log
        self.max_lines = max_lines

    def extract_errors(self):
        lines = self.raw_log.splitlines()
        pattern = re.compile(r"(error|exception|failed|fail|traceback)", re.IGNORECASE)
        last_idx = max(0, len(lines) - self.max_lines)
        last_line_indexes = set(range(last_idx, len(lines)))
        error_indexes = set(i for i, ln in enumerate(lines) if pattern.search(ln))
        relevant = sorted(last_line_indexes.union(error_indexes))
        secret_pattern = re.compile(r"(password|token)\S*", re.IGNORECASE)
        result = []
        for i in relevant:
            sanitized = secret_pattern.sub("[REDACTED]", lines[i])
            result.append(sanitized.strip())
        return "\n".join(result)

class LocalLLMClient:
    def __init__(self):
        self.llm_url = os.getenv("LLM_API_URL", "http://llm-api-container:8000/predict")

    def analyze_errors(self, text):
        prompt = "Hier sind die Logzeilen:\n\n" + text
        try:
            r = requests.post(self.llm_url, json={"prompt": prompt}, timeout=30)
            r.raise_for_status()
            return r.json().get("response", "")
        except Exception as e:
            return "Fehler bei der Anfrage an das lokale LLM: {e}"

class BuildAnalyzer:
    def __init__(self, jenkins_base_url, job_name, build_number, jenkins_user, jenkins_token):
        self.log_fetcher = JenkinsLogFetcher(jenkins_base_url, job_name, build_number, jenkins_user, jenkins_token)
        self.llm_client = LocalLLMClient()

    def run_analysis(self):
        raw_log = self.log_fetcher.get_console_log()
        if not raw_log:
            print("Konnte kein Log abrufen.")
            return
        parser = LogParser(raw_log, max_lines=50)
        relevant_text = parser.extract_errors()
        if not relevant_text.strip():
            print("Kein relevanter Fehler gefunden.")
            return
        analysis_result = self.llm_client.analyze_errors(relevant_text)
        print(analysis_result)

def main():
    base_url = "https://llm-lokal-jenkins-0.comquent.academy/"
    job_name = os.getenv("FAILED_JOB_NAME")
    build_number = os.getenv("FAILED_BUILD_NUMBER")
    jenkins_user = "training"
    jenkins_token = os.getenv("JENKINS_API_TOKEN")
    try:
        analyzer = BuildAnalyzer(base_url, job_name, build_number, jenkins_user, jenkins_token)
        analyzer.run_analysis()
    except Exception as e:
        print(f"Fehler: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
