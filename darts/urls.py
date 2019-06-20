from django.urls import path
from.import views

app_name= 'darts'

urlpatterns=[
    path('',views.index,name='darts'),

]