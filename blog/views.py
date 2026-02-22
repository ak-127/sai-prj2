from django.shortcuts import render
from .models import Blog, Category
from django.utils import timezone

def blog(request):
    blogs=Blog.objects.all()
    category=Category.objects.all()
    midpoint = len(category) // 2
    first_half = category[:midpoint]
    second_half = category[midpoint:]
    context = {
        'first_half': first_half, 
        'second_half': second_half,
        'blogs': blogs
        }
    return render(request, 'blog/all_blog.html', context)

def blog_post(request, id):
    blogs=Blog.objects.all()
    blog= Blog.objects.get(id=id)
    context = {'blog':blog,'blogs':blogs}
    return render(request, 'blog/blog_post.html', context)
