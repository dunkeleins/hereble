# bledata/api_views.py (oder views.py, je nach Aufbau)
from django.http import JsonResponse
from django.utils.timezone import make_aware, now
from datetime import datetime, timedelta
from bledata.models import BLEData
from django.views.decorators.csrf import csrf_exempt

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
        "mac", "rssi", "name", "timestamp"
    ).order_by("-timestamp")
    
    if mac_list and mac_list != [""]:
        data = data.filter(mac__in=mac_list)

    return JsonResponse(list(data), safe=False)

def mac_list(request):
    # filter auf rssi > -30
    macs = BLEData.objects.filter(rssi__gt=-30).values_list("mac", flat=True).distinct().order_by("mac")
    return JsonResponse(list(macs), safe=False)

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
    for mac in macs:
        data = BLEData.objects.filter(mac=mac, timestamp__range=(start, end)) \
                              .order_by("timestamp") \
                              .values("timestamp", "rssi")
        result[mac] = [
            {"timestamp": d["timestamp"].isoformat(), "rssi": d["rssi"]} for d in data
        ]

    return JsonResponse(result)