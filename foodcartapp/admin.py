from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from .models import Product, Order, Products
from .models import ProductCategory
from .models import Restaurant
from .models import RestaurantMenuItem


class RestaurantMenuItemInline(admin.TabularInline):
    model = RestaurantMenuItem
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'address',
        'contact_phone',
    ]
    list_display = [
        'name',
        'address',
        'contact_phone',
    ]
    inlines = [
        RestaurantMenuItemInline
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'get_image_list_preview',
        'name',
        'category',
        'price',
    ]
    list_display_links = [
        'name',
    ]
    list_filter = [
        'category',
    ]
    search_fields = [
        # FIXME SQLite can not convert letter case for cyrillic words properly, so search will be buggy.
        # Migration to PostgreSQL is necessary
        'name',
        'category__name',
    ]

    inlines = [
        RestaurantMenuItemInline
    ]
    fieldsets = (
        ('Общее', {
            'fields': [
                'name',
                'category',
                'image',
                'get_image_preview',
                'price',
            ]
        }),
        ('Подробно', {
            'fields': [
                'special_status',
                'description',
            ],
            'classes': [
                'wide'
            ],
        }),
    )

    readonly_fields = [
        'get_image_preview',
    ]

    class Media:
        css = {
            "all": (
                static("admin/foodcartapp.css")
            )
        }

    def get_image_preview(self, obj):
        if not obj.image:
            return 'выберите картинку'
        return format_html('<img src="{url}" style="max-height: 200px;"/>', url=obj.image.url)
    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html('<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>', edit_url=edit_url, src=obj.image.url)
    get_image_list_preview.short_description = 'превью'


@admin.register(ProductCategory)
class ProductAdmin(admin.ModelAdmin):
    pass


class ProductsInline(admin.TabularInline):
    model = Products
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', ]
    fields = (
        ('firstname', 'lastname'),
        ('phonenumber', 'address'),
        'payment_method',
        'created_at',
        ('called_at', 'delivered_at'),
        ('restaurant', 'status'),
        ('lat', 'lon'),
    )
    list_display = [
        'firstname',
        'lastname',
        'phonenumber',
        'address',
    ]
    list_display_links = [
        'lastname',
    ]
    list_filter = [
        'phonenumber',
        'lastname',
        'status',
    ]
    search_fields = [
        # FIXME SQLite can not convert letter case for cyrillic words properly, so search will be buggy.
        # Migration to PostgreSQL is necessary
        'lastname',
        'phonenumber',
        'address',
    ]

    inlines = [
        ProductsInline
    ]

    def response_change(self, request, obj):
        res = super(OrderAdmin, self).response_change(request, obj)
        if "next" in request.GET:
            redirect_to = request.GET['next']
            url_is_safe = url_has_allowed_host_and_scheme(
                url=redirect_to,
                allowed_hosts=settings.ALLOWED_HOSTS,
                require_https=request.is_secure(),
                )
            if url_is_safe:
                if obj.restaurant:
                    if obj.status == Order.Statuses.PENDING:
                        obj.status = Order.Statuses.ASSEMBLY
                        obj.save()
                return HttpResponseRedirect(request.GET['next'])
        return res
