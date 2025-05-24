from django.test import TestCase

# Tests für die BLE-Daten-API
class BLEDataAPITests(TestCase):
    def setUp(self):
        # Hier können Testdaten erstellt werden, die in den Tests verwendet werden
        pass

    def test_bledata_json(self):
        # Test für die bledata_json-API-View
        response = self.client.get('/api/bledata/json/')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, [])

    def test_mac_list(self):
        # Test für die mac_list-API-View
        response = self.client.get('/api/bledata/macs/')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, [])

    def test_rssi_data(self):
        # Test für die rssi_data-API-View
        response = self.client.get('/api/bledata/rssi/', {'macs': '00:11:22:33:44:55'})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {})

    def test_available_days(self):
        # Test für die available_days-API-View
        response = self.client.get('/api/bledata/days/')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"days": []})
