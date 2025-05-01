from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    path('bledata/', views.bledata, name='bledata'),
    path('sendbledata/', views.receive_ble_data, name='receive_ble_data'),    
    path('listbledata/', views.list_ble_data, name='list_ble_data'),
    path('showgraph/', views.show_graph, name='show_graph'),
    path('db_analyze_01/', views.db_analyze_group_by, name='db_analyze_group_by'),
    path('db_analyze_02/', views.db_analyze_graph_by_date, name='db_analyze_graph_by_date'),
    path('db_analyze_03/', views.generate_minute_table, name='generate_minute_table'),
    path("api/bledata", api_views.bledata_json, name="bledata_json"),
    path('api/mac_list', api_views.mac_list, name='mac_list'),
    path('api/rssi_data', api_views.rssi_data, name='rssi_data'),
    path('api/rssi_chart_data', api_views.rssi_chart_data, name='rssi_chart_data'),
    path('api/available_days', api_views.available_days, name='available_days'),
]