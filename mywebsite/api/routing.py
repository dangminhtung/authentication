from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    
    re_path(r'ws/qrcode/$', consumers.Scantest.as_asgi()),
    re_path(r'ws/qrcodev2/$', consumers.ScanQR_and_Face.as_asgi())
]
