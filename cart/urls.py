from django.conf.urls import patterns, url

from cart import views

urlpatterns = patterns('',
    url(r'^$', views.cart),
    url(r'^checkout$', views.checkout),
)
