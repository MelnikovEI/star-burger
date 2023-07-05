import django.http
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from phonenumber_field.phonenumber import PhoneNumber
from phonenumbers import NumberParseException
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Product, Order, OrderElement


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def is_positive_integer(val):
    if not isinstance(val, int):
        return False
    elif val < 1:
        return False
    return True


@api_view(['POST'])
def register_order(request):
    try:
        order_data = request.data  # json.loads(request.body.decode())
    except ValueError:
        return Response({'error': 'No data returned in order'}, status=status.HTTP_417_EXPECTATION_FAILED)

    try:
        order_elements = order_data['products']
        first_name = order_data['firstname']
        last_name = order_data['lastname']
        phone_number_str = order_data['phonenumber']
        address = order_data['address']
    except KeyError as e:
        return Response({'error': f'The key {e} is not specified'}, status=status.HTTP_417_EXPECTATION_FAILED)

    if not order_elements:
        return Response({'error': f"'Products' can\'t be empty"}, status=status.HTTP_417_EXPECTATION_FAILED)

    try:
        if not isinstance(order_elements, list):
            raise TypeError('products')
        if not isinstance(first_name, str):
            raise TypeError('firstname')
        if not isinstance(last_name, str):
            raise TypeError('lastname')
        if not isinstance(phone_number_str, str):
            raise TypeError('phonenumber')
        if not isinstance(address, str):
            raise TypeError('address')
    except TypeError as e:
        return Response({'error': f"The key '{e}' has wrong type"},
                        status=status.HTTP_417_EXPECTATION_FAILED)
    try:
        phone_number = PhoneNumber.from_string(phone_number=phone_number_str, region='RU')
        if not phone_number.is_valid():
            raise ValueError(phone_number_str)
    except (NumberParseException, ValueError) as e:
        return Response({'error': f"The phone number is incorrect: '{e}'"},
                        status=status.HTTP_417_EXPECTATION_FAILED)

    order = Order.objects.create(
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        address=address,
    )
    for element in order_elements:
        product_id = element['product']
        if not is_positive_integer(product_id):
            return Response(
                {'error': f"Product_id '{product_id}' is not positive integer"},
                status=status.HTTP_417_EXPECTATION_FAILED
            )
        try:
            product = get_object_or_404(Product, pk=product_id)
        except django.http.Http404:
            return Response(
                {'error': f"Product '{product_id}' doesn\'t exist"},
                status=status.HTTP_404_NOT_FOUND
            )
        quantity = element['quantity']
        if not is_positive_integer(quantity):
            return Response(
                {'error': f"Quantity '{quantity}' is not positive integer"},
                status=status.HTTP_417_EXPECTATION_FAILED,
            )
        OrderElement.objects.create(
            product=product,
            quantity=quantity,
            order=order,
        )
    return Response({}, status=status.HTTP_201_CREATED)
