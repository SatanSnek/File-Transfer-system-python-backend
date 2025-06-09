from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register_user, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('upload/', views.upload_file, name='upload_file'),
    path('files/', views.file_list, name='file_list'),
    path('transfer/<int:file_id>/', views.transfer_file, name='transfer_file'),
    path('logs/', views.file_logs, name='file_logs'),
    path('pending/', views.pending_files, name='pending_files'),  # New
    path('accept/<int:log_id>/', views.accept_file, name='accept_file'),  # New
    path('download/<int:file_id>/', views.download_file, name='download_file'),  # New
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)