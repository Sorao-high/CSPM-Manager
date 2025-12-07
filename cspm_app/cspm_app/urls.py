from django.contrib import admin
from django.urls import path
from management.views import (
    DashboardView, AccountListView, AccountCreateView,
    MonitorGroupUpdateView, MonitorGroupDeleteView,
    CloudAccountUpdateView, CloudAccountDeleteView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', DashboardView.as_view(), name='dashboard'),
    path('accounts/', AccountListView.as_view(), name='account_list'),
    path('accounts/add/', AccountCreateView.as_view(), name='account_add'),
    
    # 追加: 監視グループの操作
    path('groups/<int:pk>/edit/', MonitorGroupUpdateView.as_view(), name='group_edit'),
    path('groups/<int:pk>/delete/', MonitorGroupDeleteView.as_view(), name='group_delete'),

    # 追加: アカウントの操作
    path('accounts/<int:pk>/edit/', CloudAccountUpdateView.as_view(), name='account_edit'),
    path('accounts/<int:pk>/delete/', CloudAccountDeleteView.as_view(), name='account_delete'),
]