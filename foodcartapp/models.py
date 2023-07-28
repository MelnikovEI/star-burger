import requests
from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import F, Sum, signals
from django.dispatch import receiver
from phonenumber_field.modelfields import PhoneNumberField
from django.conf import settings


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
    )
    lat = models.FloatField('Координаты ресторана: широта (latitude)', null=True, blank=True)
    lon = models.FloatField('Координаты ресторана: долгота (longitude)', null=True, blank=True)
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена в каталоге',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def order_price(self):
        return self.annotate(order_price=Sum(F('products__quantity') * F('products__fixed_price')))


class Order(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('EL', 'Электронно'),
        ('CS', 'Наличностью'),
    ]
    payment_method = models.CharField(
        max_length=2,
        choices=PAYMENT_METHOD_CHOICES,
        default='CS',
    )

    class Statuses(models.IntegerChoices):
        PENDING = 1, 'Обработать'
        ASSEMBLY = 2, 'Собрать'
        DELIVER = 3, 'Доставить'
        FINISHED = 4, 'Выполнен'
    status = models.IntegerField(
        choices=Statuses.choices,
        default=Statuses.PENDING,
    )
    firstname = models.CharField('Имя', max_length=50)
    lastname = models.CharField('Фамилия', max_length=50)
    phonenumber = PhoneNumberField('Номер телефона', region='RU')
    address = models.CharField('Адрес доставки', max_length=100)
    lat = models.FloatField('Координаты доставки: широта (latitude)', null=True, blank=True)
    lon = models.FloatField('Координаты доставки: долгота (longitude)', null=True, blank=True)
    comment = models.TextField('Комментарий', max_length=500, blank=True)
    created_at = models.DateTimeField('Заказ создан', auto_now_add=True)
    called_at = models.DateTimeField('Звонок совершён', null=True, blank=True)
    delivered_at = models.DateTimeField('Доставлен', null=True, blank=True)
    restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='Ресторан - исполнитель заказа',
        related_name='orders',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        indexes = [
            models.Index(
                fields=[
                    'lastname', 'firstname', 'phonenumber',
                    'status', 'created_at', 'called_at',
                    'delivered_at', 'payment_method'
                ]
            ),
        ]

    def __str__(self):
        return f"{self.firstname} {self.lastname} {self.address}"


class Products(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='order_elements',
        verbose_name='товар',
    )
    quantity = models.PositiveSmallIntegerField('Количество', validators=[MinValueValidator(1)])
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='элемент заказа',
    )
    fixed_price = models.DecimalField(
        'Цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'элемент заказа'
        verbose_name_plural = 'элементы заказа'

    def price(self):
        return self.quantity * self.fixed_price


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lat, lon


@receiver(signals.pre_save, sender=Restaurant)
@receiver(signals.pre_save, sender=Order)
def update_coords_if_address_changed(sender, instance, **kwargs):
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:  # Object is new, so field hasn't technically changed
        old_address = ''
    else:
        old_address = obj.address

    if not old_address == instance.address:  # Field has changed
        if instance.address:
            try:
                coords = fetch_coordinates(settings.YANDEX_GEOCODER_API_KEY, instance.address)
            except requests.RequestException:
                return
            if coords:
                instance.lat, instance.lon = coords

