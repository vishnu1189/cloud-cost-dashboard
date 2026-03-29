import requests


def get_usd_to_eur_rate() -> float:
    url = "https://api.frankfurter.dev/v1/latest?base=USD&symbols=EUR"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()

    if "rates" not in data or "EUR" not in data["rates"]:
        raise ValueError("EUR exchange rate not found in API response.")

    return float(data["rates"]["EUR"])


def get_risk_label(severity: str) -> str:
    if severity == "High":
        return "Critical Risk"
    elif severity == "Medium":
        return "Medium Risk"
    elif severity == "Low":
        return "Low Risk"
    return "Normal Risk"
    
import os
import time
from google import genai


def generate_ai_summary(service, expected_cost, actual_cost, spike_percentage, severity):
    import os
    import time
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return "GEMINI_API_KEY is not configured."

    prompt = f"""
You are a cloud cost analysis assistant.

Write a short professional summary for this anomaly:
- Service: {service}
- Expected Cost: {expected_cost} USD
- Actual Cost: {actual_cost} USD
- Spike Percentage: {spike_percentage}%
- Severity: {severity}

Keep it concise, clear, and relevant to cloud cost monitoring.
"""

    delays = [2, 4]

    try:
        client = genai.Client(api_key=api_key)

        for i, delay in enumerate(delays):
            try:
                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=prompt
                )

                if response.text:
                    return response.text.strip()

            except Exception as e:
                print("Gemini error:", str(e))
                error_text = str(e)

                if "503" in error_text or "UNAVAILABLE" in error_text:
                    if i < len(delays) - 1:
                        time.sleep(delay)
                        continue
                    return "AI summary temporarily unavailable."

                return "AI summary temporarily unavailable due to API quota limits."

        return "AI summary unavailable."

    except Exception as e:
        print("Gemini setup error:", str(e))
        return "AI summary temporarily unavailable."
