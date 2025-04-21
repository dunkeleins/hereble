from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    path('bledata/', views.bledata, name='bledata'),
    path('sendbledata/', views.receive_ble_data, name='receive_ble_data'),    
    path('listbledata/', views.list_ble_data, name='list_ble_data'),
    path('showgraph/', views.show_graph, name='show_graph'),
    path("api/bledata", api_views.bledata_json, name="bledata_json"),
    path('api/mac_list', api_views.mac_list, name='mac_list'),
    path('api/rssi_data', api_views.rssi_data, name='rssi_data'),
]