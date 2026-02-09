from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.db.models import Q
from datetime import datetime, timedelta

from .models import Customer, LedgerEntry
from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer,
    CustomerSerializer,
    LedgerEntrySerializer,
    CustomerSummarySerializer
)


class UserRegistrationView(APIView):

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Successfully registered',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class UserLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Successfully logged in',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class CustomerViewSet(viewsets.ModelViewSet):
    
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Disable pagination for customers list

    def get_queryset(self):
        #Only show customers of the logged-in user
        return Customer.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '').strip()
        if not query or len(query) < 2:
            return Response({
                'error': 'At least 2 characters required for search'
            }, status=status.HTTP_400_BAD_REQUEST)

        customers = self.get_queryset().filter(
            Q(name__icontains=query) | Q(phone__icontains=query)
        )
        serializer = self.get_serializer(customers, many=True)
        return Response(serializer.data)


    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        customer = self.get_object()
        serializer = CustomerSummarySerializer(customer)
        return Response(serializer.data)



class LedgerEntryViewSet(viewsets.ModelViewSet):
    serializer_class = LedgerEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # শুধুমাত্র current user এর customers এর entries দেখাবে 
        return LedgerEntry.objects.filter(
            customer__user=self.request.user
        ).select_related('customer')

    def perform_create(self, serializer):
        #নতুন entry তৈরি করার সময় customer verify করা
        customer_id = self.request.data.get('customer')
        try:
            customer = Customer.objects.get(id=customer_id, user=self.request.user)
            serializer.save(customer=customer)
        except Customer.DoesNotExist:
            return Response({
                'error': 'Not found'
            }, status=status.HTTP_404_NOT_FOUND)

    def get_serializer_context(self):
        """Pass context to the serializer for nested serialization and user-specific data"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=False, methods=['get'])
    def by_customer(self, request):
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response({
                'error': 'customer_id Needed'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            customer = Customer.objects.get(id=customer_id, user=request.user)
        except Customer.DoesNotExist:
            return Response({
                'error': 'Customer not found'
            }, status=status.HTTP_404_NOT_FOUND)

        entries = customer.ledger_entries.all()
        serializer = self.get_serializer(entries, many=True)
        return Response({
            'customer': {
                'id': customer.id,
                'name': customer.name
            },
            'entries': serializer.data,
            'summary': customer.get_summary()
        })

    @action(detail=False, methods=['get'])
    def filter_by_date(self, request):
        customer_id = request.query_params.get('customer_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not customer_id:
            return Response({
                'error': 'customer_id Needed'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            customer = Customer.objects.get(id=customer_id, user=request.user)
        except Customer.DoesNotExist:
            return Response({
                'error': 'Customer not found'
            }, status=status.HTTP_404_NOT_FOUND)

        entries = customer.ledger_entries.all()

        # Start date ফিল্টার
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                entries = entries.filter(entry_date__gte=start)
            except ValueError:
                return Response({
                    'error': 'Invalid start date format (YYYY-MM-DD expected)'
                }, status=status.HTTP_400_BAD_REQUEST)

        # End date ফিল্টার
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                entries = entries.filter(entry_date__lte=end)
            except ValueError:
                return Response({
                    'error': 'Invalid end date format (YYYY-MM-DD expected)'
                }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(entries, many=True)
        return Response({
            'customer': {
                'id': customer.id,
                'name': customer.name
            },
            'date_range': {
                'start': start_date,
                'end': end_date
            },
            'entries': serializer.data,
            'total_entries': entries.count()
        })

    @action(detail=False, methods=['get'])
    def filter_by_type(self, request):
        customer_id = request.query_params.get('customer_id')
        entry_type = request.query_params.get('type')

        if not customer_id:
            return Response({
                'error': 'customer_id Needed'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not entry_type or entry_type not in ['CREDIT', 'DEBIT']:
            return Response({
                'error': 'type must be CREDIT or DEBIT'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            customer = Customer.objects.get(id=customer_id, user=request.user)
        except Customer.DoesNotExist:
            return Response({
                'error': 'Customer not found'
            }, status=status.HTTP_404_NOT_FOUND)

        entries = customer.ledger_entries.filter(type=entry_type)
        serializer = self.get_serializer(entries, many=True)
        
        total = sum(float(entry.amount) for entry in entries)
        
        return Response({
            'customer': {
                'id': customer.id,
                'name': customer.name
            },
            'type': entry_type,
            'entries': serializer.data,
            'total_amount': total,
            'entries_count': entries.count()
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        customers = Customer.objects.filter(user=request.user)
        
        stats = {
            'total_customers': customers.count(),
            'total_credit': 0,
            'total_debit': 0,
            'total_balance': 0,
            'total_entries': 0
        }

        for customer in customers:
            summary = customer.get_summary()
            stats['total_credit'] += float(summary['total_credit'])
            stats['total_debit'] += float(summary['total_debit'])
            stats['total_balance'] += float(summary['balance'])
            stats['total_entries'] += customer.ledger_entries.count()

        return Response(stats)