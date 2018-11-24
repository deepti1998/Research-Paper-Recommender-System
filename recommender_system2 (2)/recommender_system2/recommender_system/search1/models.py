from django.db import models
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User


class Urls(models.Model):
    url = models.CharField(max_length=2083, primary_key=True)
    title = models.TextField()

    def __str__(self):
        return self.url


class Keywords_Search(models.Model):
    keyword = models.CharField(max_length=100, primary_key=True)
    search = models.BooleanField()

    def __str__(self):
        return self.keyword


class Keywords_Count(models.Model):
    id = models.AutoField(primary_key=True)
    keyword = models.ForeignKey(Keywords_Search, on_delete=models.CASCADE)
    url = models.ForeignKey(Urls, on_delete=models.CASCADE)
    count = models.IntegerField()

    def __str__(self):
        return self.url.url

