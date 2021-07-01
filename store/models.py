from django.db import models
from django.db.models.signals import pre_save, post_save
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.shortcuts import reverse
from datetime import datetime


payment_choices = (
    ('STRIP', 'STRIP'),
    ('COD', 'COD'),
)


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    description = models.TextField(max_length=600, null=True, blank=True)
    image = models.ImageField(null=True, blank=True)
    price = models.IntegerField(null=True, blank=True)
    category = models.ManyToManyField(Category)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("product", kwargs={
            'slug': self.slug
        })


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=100, choices=payment_choices, blank=True, null=True)
    shipping_address = models.ForeignKey(
        'Address', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    ordered_date = models.DateTimeField(blank=True, null=True)
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, blank=True, null=True)

    def get_total(self):
        total = 0
        for i in self.orderitem_set.all():
            total += i.get_price()
        return total

    def delete(self, *args, **kwargs):
        if self.shipping_address.default is False:
            self.shipping_address.delete()
        super(Order, self).delete(*args, **kwargs)

    def get_quantity(self):
        total = 0
        for i in self.orderitem_set.all():
            total += i.quantity
        return total

    def __str__(self):
        return f"Price {str(self.get_total())}$ and quantity {str(self.get_quantity())} order for {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def get_price(self):
        return self.quantity * self.product.price

    def __str__(self):
        return f"{self.quantity} of {self.product.name}"


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True, null=True)
    full_address = models.CharField(max_length=100)
    phone = models.CharField(max_length=100)
    default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} of {self.full_address}"


class Payment(models.Model):
    strip_token_id = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()

    def __str__(self):
        return f"{self.user.username} -- Order amount: {self.amount}$"


@receiver(pre_save, sender=Product)
def my_callback(sender, instance, *args, **kwargs):
    instance.slug = slugify(instance.name)


@receiver(post_save, sender=User)
def my_callback(sender, instance, created, *args, **kwargs):
    if created:
        g = Group.objects.get(name='customer')
        instance.groups.add(g)