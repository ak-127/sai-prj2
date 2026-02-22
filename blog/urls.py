from django.urls import path
from . import views


urlpatterns = [
    path('', views.blog, name='blogs'),
    path('<int:id>', views.blog_post, name='blog-post')
]
