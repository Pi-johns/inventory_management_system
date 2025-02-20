from rest_framework import serializers
from .models import SalesReport, ProductPerformance

class SalesReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesReport
        fields = '__all__'

class ProductPerformanceSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = ProductPerformance
        fields = ['product_name', 'total_sold', 'total_revenue']
