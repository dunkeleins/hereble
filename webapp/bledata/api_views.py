# bledata/api_views.py 
# Django API-Views für BLE-Daten
# Diese Views liefern JSON-Daten für BLE-Daten, MAC-Listen und RSSI-Daten.
from django.http import JsonResponse
from django.utils.timezone import make_aware, now
from datetime import datetime, timedelta
from bledata.models import BLEData
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import numpy as np  
from django.db.models.functions import TruncDate
from django.db.models import OuterRef, Subquery
from django.utils.dateparse import parse_datetime



# API-View, um BLE-Daten als JSON zu liefern
@csrf_exempt
def bledata_json(request):
    start_str = request.GET.get("start")
    end_str = request.GET.get("end")
    mac_list = request.GET.get("macs", "").split(",")

    try:
        start = make_aware(datetime.fromisoformat(start_str)) if start_str else now() - timedelta(hours=1)
        end = make_aware(datetime.fromisoformat(end_str)) if end_str else now()
    except ValueError:
        return JsonResponse({"error": "Invalid datetime format"}, status=400)

    data = BLEData.objects.filter(timestamp__range=(start, end)).values(
        "mac_hash", "rssi", "name", "timestamp"
    ).order_by("-timestamp")
    
    if mac_list and mac_list != [""]:
        data = data.filter(mac_hash__in=mac_list)

    return JsonResponse(list(data), safe=False)

# Listet alle eindeutigen MAC-Hashes, die einen RSSI-Wert größer als -30 haben
def mac_list(request):
    # filter auf rssi > -30
    macs = BLEData.objects.filter(rssi__gt=-30).values_list("mac_hash", flat=True).distinct().order_by("mac_hash")
    return JsonResponse(list(macs), safe=False)

# Liefert RSSI-Daten für eine Liste von MAC-Hashes in einem bestimmten Zeitbereich
def rssi_data(request):
    macs = request.GET.get("macs", "").split(",")
    start_str = request.GET.get("start")
    end_str = request.GET.get("end")

    try:
        start = make_aware(datetime.fromisoformat(start_str))
        end = make_aware(datetime.fromisoformat(end_str))
    except Exception:
        return JsonResponse({"error": "Invalid date format"}, status=400)

    result = {}
    for mac_hash in macs:
        data = BLEData.objects.filter(mac_hash=mac_hash, timestamp__range=(start, end)) \
                              .order_by("timestamp") \
                              .values("timestamp", "rssi")
        result[mac_hash] = [
            {"timestamp": d["timestamp"].isoformat(), "rssi": d["rssi"]} for d in data
        ]

    return JsonResponse(result)

# Liefert eine Liste aller Tage, an denen BLE-Daten vorhanden sind
def available_days(request):
    days = BLEData.objects.annotate(day=TruncDate("timestamp")).values_list("day", flat=True).distinct().order_by("day")
    return JsonResponse({"days": list(days)})

# Liefert die RSSI-Daten für ein bestimmtes Gerät (MAC-Hash) in einem bestimmten Zeitbereich
def rssi_chart_data(request):
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    name = request.GET.get("name", "").split(",")

    try:
        start = make_aware(datetime.fromisoformat(start_str)) if start_str else now() - timedelta(hours=1)
        end = make_aware(datetime.fromisoformat(end_str)) if end_str else now()
    except ValueError:
        start = now() - timedelta(hours=1)
        end = now()
    
    queryset = BLEData.objects.filter(timestamp__range=(start, end)).values("timestamp", "name", "rssi")
    for n in name:
        if n != "":
            queryset = queryset.filter(name__icontains=n)

    df = pd.DataFrame(list(queryset))

    if df.empty:
        return JsonResponse({"datasets": []})

    df["name"] = df["name"].replace({None: "Others", "": "Others"})
    df["rounded_time"] = pd.to_datetime(df["timestamp"]).dt.floor("5s")

    grouped = df.groupby(["name", "rounded_time"])["rssi"].agg(["min", "max", "mean"]).reset_index()

    datasets = []
    colors = [
        "#3b82f6", "#10b981", "#ef4444", "#f59e0b", "#8b5cf6", "#ec4899", "#14b8a6"
    ]

    for idx, (name, group) in enumerate(grouped.groupby("name")):
        color = colors[idx % len(colors)]

        # Mittelwert-Linie
        datasets.append({
            "label": f"{name} (Mean)",
            "data": [{"x": ts.isoformat(), "y": val} for ts, val in zip(group["rounded_time"], group["mean"])],
            "borderColor": color,
            "backgroundColor": color,
            "fill": False,
            "tension": 0.3
        })

        # Min-Max Fläche
        datasets.append({
            "label": f"{name} (Max)",
            "data": [
                { "x": ts.isoformat(), "y": val }
                for ts, val in zip(group["rounded_time"], group["max"])
            ],
            "fill": {
                "target": {
                    "x": group["rounded_time"].iloc[0].isoformat(),  # Dummy
                    "y": 0
                },
                "above": color + "33",  # 20% Deckkraft
                "below": color + "33"
            },
            "fill": "+1",
            "pointRadius": 0,
            "borderWidth": 0,
            "backgroundColor": color + "33",  # 20% Deckkraft
            "type": "line"
        })

        # Optional: Min-Werte als Linie
        datasets.append({
            "label": f"{name} (Min)",
            "data": [{"x": ts.isoformat(), "y": val} for ts, val in zip(group["rounded_time"], group["min"])],
            "borderDash": [5, 5],
            "borderColor": color,
            "backgroundColor": color,
            "fill": "false",
            "pointRadius": 0,
            "borderWidth": 0,
            "tension": 0.3
         })

    return JsonResponse({"datasets": datasets})