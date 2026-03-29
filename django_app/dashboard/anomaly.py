import pandas as pd


def get_severity(spike_percentage: float) -> str:
    if spike_percentage > 100:
        return "High"
    elif spike_percentage > 50:
        return "Medium"
    elif spike_percentage > 20:
        return "Low"
    return "Normal"


def generate_explanation(service: str, actual: float, expected: float, spike_percentage: float) -> str:
    severity = get_severity(spike_percentage)

    if severity == "High":
        return (
            f"{service} shows a major cost spike. "
            f"Actual cost is {actual:.2f} USD versus expected cost of {expected:.2f} USD."
        )
    elif severity == "Medium":
        return (
            f"{service} spend is noticeably above normal. "
            f"Actual cost is {actual:.2f} USD compared with expected cost of {expected:.2f} USD."
        )
    else:
        return (
            f"{service} spend is slightly higher than usual. "
            f"Actual cost is {actual:.2f} USD compared with expected cost of {expected:.2f} USD."
        )


def detect_anomalies(df: pd.DataFrame):
    anomalies = []

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by=["service", "date"])

    for service, group in df.groupby("service"):
        group = group.reset_index(drop=True)

        for i in range(1, len(group)):
            previous_rows = group.loc[: i - 1, "cost_usd"]
            expected_cost = float(previous_rows.mean())
            actual_cost = float(group.loc[i, "cost_usd"])

            if expected_cost == 0:
                continue

            spike_percentage = float(((actual_cost - expected_cost) / expected_cost) * 100)

            if spike_percentage > 20:
                severity = get_severity(spike_percentage)

                anomalies.append(
                    {
                        "date": str(group.loc[i, "date"].date()),
                        "service": str(service),
                        "expected_cost_usd": round(expected_cost, 2),
                        "actual_cost_usd": round(actual_cost, 2),
                        "spike_percentage": round(spike_percentage, 2),
                        "severity": severity,
                        "explanation": generate_explanation(
                            str(service), actual_cost, expected_cost, spike_percentage
                        ),
                    }
                )

    return anomalies