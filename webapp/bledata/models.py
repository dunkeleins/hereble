from django.db import models

# Create your models here.
class BLEData(models.Model):
    mac = models.CharField(max_length=100)
    mac_hash = models.CharField(max_length=100)
    rssi = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    distance = models.FloatField()
    service_uuid = models.CharField(max_length=100)
    manufacturer_data = models.CharField(max_length=100)
    environment = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name