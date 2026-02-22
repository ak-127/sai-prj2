from PIL import Image
from django.db import models
from django.utils import timezone



class Category(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name


class Blog(models.Model):
    title = models.CharField(max_length=25)
    feature_image = models.ImageField(upload_to='blog_feature_image/')
    content =   models.TextField()
    category = models.ManyToManyField(Category, related_name='blogs')
    author = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    publish_date = models.DateTimeField(default=timezone.now)



    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.feature_image.path)

        if img.height != 900 or img.width != 400:
            img = img.resize((900, 400), Image.Resampling.LANCZOS)
            img.save(self.feature_image.path)
