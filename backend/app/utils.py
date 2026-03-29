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