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
import json
from .models import BLEData

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
                    mac=device.get("mac"),
                    rssi=device.get("rssi"),
                    name=device.get("name"),
                    distance=device.get("distance"),
                    service_uuid=device.get("service_uuid", ""),  # Optional
                    manufacturer_data=device.get("manufacturer_data", ""),  # Optional
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
        .values('mac')
        .annotate(max_rssi=Max('rssi'))
        .order_by('-max_rssi')[:2]
    )

    datasets = []
    labels_set = set()

    for mac_entry in top_macs:
        mac = mac_entry['mac']
        data_points = (
            BLEData.objects
            .filter(mac=mac, timestamp__range=(start, end))
            .order_by('timestamp')
        )

        timestamps = [dp.timestamp.strftime("%H:%M:%S") for dp in data_points]
        rssi_values = [dp.rssi for dp in data_points]

        labels_set.update(timestamps)

        datasets.append({
            "label": f"{mac}",
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
        .values("mac", "hour")
        .annotate(count=Count("id"),
                  rssi=Max("rssi")
        )
        .order_by("-hour", "mac")
    )

    return render(request, "ble_list.html", {"ble_entries": top_rssi_last_hour})
