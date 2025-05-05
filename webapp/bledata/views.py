from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Max, Min, Sum, Avg, StdDev, Variance
from django.db.models.functions import TruncHour, TruncMinute, TruncDate
from django.utils.timezone import make_aware
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from django.db.models import OuterRef, Subquery
from django.db.models.functions import TruncDate
from django.utils.dateparse import parse_datetime
import json
from .models import BLEData
import pandas as pd
import numpy as np

def bledata(request):
  template = loader.get_template('first.html')
  return HttpResponse(template.render())

@csrf_exempt
def receive_ble_data(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            devices = data.get("devices", [])
            created_ids = []

            for device in devices:
                ble_entry = BLEData.objects.create(
                    mac_hash=device.get("mac_hash"),
                    rssi=device.get("rssi"),
                    name=device.get("name"),
                    distance=device.get("distance"),
                    service_uuid=device.get("service_uuid", ""),  # Optional
                    manufacturer_data=device.get("manufacturer_data", ""),  # Optional
                    environment=device.get("environment", ""),  # Optional
                    timestamp=now()
                )
                created_ids.append(ble_entry.id)

            return JsonResponse({"status": "success", "count": len(created_ids), "ids": created_ids}, status=201)

        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({"status": "error", "message": f"Invalid JSON: {str(e)}"}, status=400)

    return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)


def show_graph(request):
    # Zeitbereich aus dem GET-Parameter lesen
    macs_str = request.GET.get("macs", "")
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    macs = macs_str.split(",") if macs_str else []

    try:
        start = make_aware(datetime.fromisoformat(start_str)) if start_str else now() - timedelta(hours=1)
        end = make_aware(datetime.fromisoformat(end_str)) if end_str else now()
    except ValueError:
        start = now() - timedelta(hours=1)
        end = now()

    # Zwei MACs mit dem höchsten RSSI im Zeitraum
    top_macs = (
        BLEData.objects
        .filter(timestamp__range=(start, end))
        .values('mac_hash')
        .annotate(max_rssi=Max('rssi'))
        .order_by('-max_rssi')[:2]
    )

    datasets = []
    labels_set = set()

    for mac_entry in top_macs:
        mac_hash = mac_entry['mac_hash']
        data_points = (
            BLEData.objects
            .filter(mac_hash=mac_hash, timestamp__range=(start, end))
            .order_by('timestamp')
        )

        timestamps = [dp.timestamp.strftime("%H:%M:%S") for dp in data_points]
        rssi_values = [dp.rssi for dp in data_points]

        labels_set.update(timestamps)

        datasets.append({
            "label": f"{mac_hash}",
            "data": rssi_values,
            "fill": False,
            "borderColor": "rgba(75,192,192,1)",
            "tension": 0.1
        })

    context = {
        "labels": sorted(labels_set),
        "datasets": datasets,
        "selected_macs": macs,
        "start": start.strftime('%Y-%m-%dT%H:%M'),
        "end": end.strftime('%Y-%m-%dT%H:%M'),
    }

    return render(request, "ble_graph.html", context)

def ble_chart_view(request):
    return render(request, "ble_graph.html")

def list_ble_data(request):
    top_rssi_last_hour = (
        BLEData.objects
        .filter(rssi__gt=-30)
        .annotate(hour=TruncMinute("timestamp"))
        .values("mac_hash", "hour", "name", "environment")
        .annotate(count=Count("id"),
                  rssi=Max("rssi"),
        )
        .order_by("-hour", "mac_hash")
    )

    return render(request, "ble_list.html", {"ble_entries": top_rssi_last_hour})

def db_analyze_group_by(request):
    data = list(BLEData.objects.all().values("timestamp", "name", "rssi", "environment"))
    if not data:
        return render(request, "db_analyze_01.html", {"html_table": "<p>No data available</p>"})
    df = pd.DataFrame(data)
    df["name"] = df["name"].replace({np.nan: "Others", "": "Others"})
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["interval"] = df["timestamp"].dt.floor("5s")
    result = df.groupby(["interval", "name", "environment"]).agg(
        avg_rssi=("rssi", "mean"),
        min_rssi=("rssi", "min"),
        max_rssi=("rssi", "max"),
        count=("rssi", "count"),
    ).reset_index()
    html_table = result.to_html(index=False)

    # Die Tabelle an das Template übergeben
    return render(request, "db_analyze_01.html", {"html_table": html_table})

def db_analyze_graph_by_date(request):
    return render(request, "db_analyze_02.html")

def generate_minute_table(request):
    # Daten holen
    data = BLEData.objects.all().values("timestamp", "name", "mac_hash")
    df = pd.DataFrame(list(data))

    if df.empty:
        return "Keine Daten vorhanden."

    # Timestamp auf volle Sekunde runden
    df["second"] = df["timestamp"].dt.floor("s")
    df["minute"] = df["timestamp"].dt.floor("min")

    df_apple = df[df["name"].str.contains("apple", case=False, na=False)]

    # Pro Sekunde und pro Gerätename nur einmal zählen (unabhängig von MACs)
    df_dedup = df_apple.drop_duplicates(subset=["second", "name"])

    # Zähle pro Minute und Name, wie viele Sekunden es gab
    counts = df_dedup.groupby(["minute", "name"]).size().unstack(fill_value=0)

    # Für alle Daten (nicht nur Apple!), wie viele einzigartige Sekunden gibt es pro Minute?
    unique_seconds = (
        df.drop_duplicates(subset=["second"])
          .groupby("minute")
          .size()
    )

    # Tabelle zusammenbauen
    result = counts.copy()
    result["Anzahl_Messungen_pro_Minute"] = unique_seconds

    # Aufräumen
    result = result.reset_index()
    result["minute"] = result["minute"] + pd.Timedelta(hours=2)
    
    # Kaufmännisch runden
    for device in counts.columns:
        result[device] = result[device].round().astype(int)

    result["Anzahl_Messungen_pro_Minute"] = result["Anzahl_Messungen_pro_Minute"].astype(int)
    
    # Ausgabe

    html_table = result.to_html(index=False, border=1)

    return render(request, "db_analyze_03.html", {"html_table": html_table})