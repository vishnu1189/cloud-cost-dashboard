from django.shortcuts import render
import requests
import pandas as pd
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .anomaly import detect_anomalies
from .utils import get_usd_to_eur_rate, get_risk_label, generate_ai_summary


def build_response(df):
    required_columns = {"date", "service", "cost_usd"}
    if not required_columns.issubset(df.columns):
        return {"error": "Input must contain date, service, and cost_usd fields."}

    anomalies = detect_anomalies(df)
    usd_to_eur_rate = get_usd_to_eur_rate()

    for item in anomalies:
        item["actual_cost_eur"] = round(item["actual_cost_usd"] * usd_to_eur_rate, 2)
        item["expected_cost_eur"] = round(item["expected_cost_usd"] * usd_to_eur_rate, 2)
        item["risk_label"] = get_risk_label(item["severity"])
        item["ai_summary"] = generate_ai_summary(
            service=item["service"],
            expected_cost=item["expected_cost_usd"],
            actual_cost=item["actual_cost_usd"],
            spike_percentage=item["spike_percentage"],
            severity=item["severity"],
        )

    total_flagged_cost_usd = round(
        sum(item["actual_cost_usd"] for item in anomalies), 2
    ) if anomalies else 0.0

    total_flagged_cost_eur = round(
        sum(item["actual_cost_eur"] for item in anomalies), 2
    ) if anomalies else 0.0

    highest_spike = round(
        max(item["spike_percentage"] for item in anomalies), 2
    ) if anomalies else 0.0

    average_spike = round(
        sum(item["spike_percentage"] for item in anomalies) / len(anomalies), 2
    ) if anomalies else 0.0

    severity_counts = {
        "high": sum(1 for item in anomalies if item["severity"] == "High"),
        "medium": sum(1 for item in anomalies if item["severity"] == "Medium"),
        "low": sum(1 for item in anomalies if item["severity"] == "Low"),
    }

    return {
        "summary": {
            "total_records": int(len(df)),
            "total_anomalies": int(len(anomalies)),
            "total_flagged_cost_usd": total_flagged_cost_usd,
            "total_flagged_cost_eur": total_flagged_cost_eur,
            "highest_spike_percentage": highest_spike,
            "average_anomaly_spike_percentage": average_spike,
            "usd_to_eur_rate": round(usd_to_eur_rate, 4),
            "severity_breakdown": severity_counts,
        },
        "anomalies": anomalies,
    }


def get_friend_job_market_data(job_title, location, country):
    url = "https://rae0ounh2b.execute-api.us-east-1.amazonaws.com/analyse-job"

    payload = {
        "job_title": job_title,
        "location": location,
        "country": country
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def home(request):
    context = {}

    job_title = request.POST.get("job_title", "Cloud Engineer")
    location = request.POST.get("location", "London")
    country = request.POST.get("country", "United Kingdom")

    friend_api_result = get_friend_job_market_data(job_title, location, country)

    context["friend_api_result"] = friend_api_result
    context["job_title"] = job_title
    context["location"] = location
    context["country"] = country

    if request.method == "POST":
        mode = request.POST.get("mode")

        try:
            if mode == "csv" and request.FILES.get("csv_file"):
                csv_file = request.FILES["csv_file"]
                df = pd.read_csv(csv_file)
                result = build_response(df)
                context["result"] = result

            elif mode == "json":
                json_text = request.POST.get("json_text", "").strip()
                records = json.loads(json_text)
                df = pd.DataFrame(records)
                result = build_response(df)
                context["result"] = result

            elif mode == "job_market":
                friend_api_result = get_friend_job_market_data(job_title, location, country)
                context["friend_api_result"] = friend_api_result

            else:
                context["error"] = "Please upload a CSV file, paste JSON data, or search the job market."

        except Exception as e:
            context["error"] = str(e)

    return render(request, "dashboard/home.html", context)


@csrf_exempt
def analyse_cost_json_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method is allowed."}, status=405)

    try:
        body = json.loads(request.body)
        df = pd.DataFrame(body)
        result = build_response(df)

        if "error" in result:
            return JsonResponse(result, status=400)

        return JsonResponse(result, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)