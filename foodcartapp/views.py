import django.http
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from phonenumber_field.phonenumber import PhoneNumber
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
        phone_number = order_data['phonenumber']
    except KeyError:
        return Response({'error': 'No phone number returned in order'}, status=status.HTTP_417_EXPECTATION_FAILED)
    try:
        order_elements = order_data['products']
    except KeyError:
        return Response({'error': 'No products list returned in order'}, status=status.HTTP_417_EXPECTATION_FAILED)
    if not isinstance(order_elements, list):
        return Response(
            {'error': f"'Products' should contain a list, not a {type(order_elements).__name__}"},
            status=status.HTTP_417_EXPECTATION_FAILED
        )
    if not order_elements:
        return Response({'error': f"'Products' can\'t be empty"}, status=status.HTTP_417_EXPECTATION_FAILED)

    order = Order.objects.create(
        first_name=order_data.get('firstname', ''),
        last_name=order_data.get('lastname', ''),
        phone_number=PhoneNumber.from_string(phone_number=phone_number, region='RU').as_e164,
        address=order_data.get('address', ''),
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
                {'error': f"Product_id '{product_id}' doesn\'t exist in database"},
                tatus=status.HTTP_404_NOT_FOUND
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
