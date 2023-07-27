from operator import itemgetter

from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views


from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


def get_ready_restaurants(order: Order):
    need_to_cook_list = set(order.products.all().values_list('product', flat=True))
    ready_restaurants = []
    for restaurant in Restaurant.objects.all():
        ready_to_cook_list = set(restaurant.menu_items.filter(availability=True).values_list('product', flat=True))
        if need_to_cook_list <= ready_to_cook_list:
            ready_restaurants.append(restaurant.name)
    return ready_restaurants


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = Order.objects.exclude(status=Order.Statuses.FINISHED).order_price()
    order_items = []
    for order in orders:
        restaurants = []
        if order.status in (Order.Statuses.ASSEMBLY, Order.Statuses.DELIVER):
            if order.restaurant:
                restaurants_summary = f'Готовит: "{order.restaurant}"'
            else:
                restaurants_summary = 'Ресторан не назначен'
        elif order.status == Order.Statuses.PENDING:
            restaurants = get_ready_restaurants(order)
            if restaurants:
                restaurants_summary = 'Может быть приготовлен ресторанами:'
            else:
                restaurants_summary = 'Заказ не может быть приготовлен ни одним из ресторанов'
        else:
            restaurants_summary = 'Заказ выполнен или статус не определён'
        order_items.append(
            {
                'id': order.id,
                'status': order.get_status_display(),
                'payment_method': order.get_payment_method_display(),
                'order_price': order.order_price,
                'client': f'{order.firstname} {order.lastname}',
                'phonenumber': order.phonenumber,
                'address': order.address,
                'comment': order.comment,
                'restaurants_summary': restaurants_summary,
                'restaurants': restaurants,
                'status_for_sorting': order.status,
            }
        )
        order_items.sort(key=itemgetter('status_for_sorting'))
    return render(request, template_name='order_items.html', context={'order_items': order_items})
