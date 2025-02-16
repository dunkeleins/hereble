from django.db import models

# Create your models here.
class BLEData(models.Model):
    mac = models.CharField(max_length=100)
    rssi = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    service_uuid = models.CharField(max_length=100)
    manufacturer_data = models.CharField(max_length=100)

    def __str__(self):
        return self.name