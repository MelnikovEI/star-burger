from rest_framework.serializers import ModelSerializer
from foodcartapp.models import Products, Order


class ProductsSerializer(ModelSerializer):
    class Meta:
        model = Products
        fields = ['product', 'quantity']


class OrderSerializer(ModelSerializer):
    products = ProductsSerializer(many=True, allow_empty=False)

    def create(self, validated_data):
        order = Order.objects.create(
            firstname=validated_data['firstname'],
            lastname=validated_data['lastname'],
            phonenumber=validated_data['phonenumber'],
            address=validated_data['address'],
        )
        products_fields = validated_data['products']
        products = [
            Products(
                order=order,
                fixed_price=fields['product'].price,
                **fields
            ) for fields in products_fields
        ]
        Products.objects.bulk_create(products)
        return order

    class Meta:
        model = Order
        fields = '__all__'
