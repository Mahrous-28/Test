from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from .models import Category, Product, InventoryItem
from .serializers import CategorySerializer, ProductSerializer, InventoryItemSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    @action(detail=True, methods=['post'])
    def update_stock(self, request, pk=None):
        try:
            product = self.get_object()
            quantity = int(request.data.get('quantity', 0))
            
            inventory_item, created = InventoryItem.objects.get_or_create(
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                inventory_item.quantity += quantity
                inventory_item.save()
            
            return Response({'status': 'stock updated'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        threshold = int(request.query_params.get('threshold', 10))
        items = InventoryItem.objects.filter(quantity__lte=threshold)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)