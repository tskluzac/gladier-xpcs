from django.urls import path
from globus_portal_framework.urls import register_custom_index
from xsd_img_index import views

app_name = 'xsd-img'
register_custom_index('xsd_img_index', ['xsd-img'])

urlpatterns = [
    path('<xsd_img_index:index>/', views.landing_page,
         name='landing-page'),
    path('<xsd_img_index:index>/data/', views.XsdImgProjectSearch.as_view(),
         name='search'),
]
