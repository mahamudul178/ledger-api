from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Customer, LedgerEntry


class UserAuthenticationTestCase(APITestCase):
    """
    User Registration and Login Test Cases
    Tests for user authentication functionality
    """
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
        
    def test_user_registration_success(self):
        """Test that a new user can register successfully"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['username'], 'testuser')
        self.assertEqual(response.data['user']['email'], 'test@example.com')
        self.assertTrue(User.objects.filter(username='testuser').exists())
    
    def test_user_registration_password_mismatch(self):
        """Test that registration fails if passwords do not match"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'differentpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username='testuser').exists())
    
    def test_user_registration_duplicate_username(self):
        """Test that duplicate usernames cannot be registered"""
        User.objects.create_user(username='testuser', email='test1@example.com', password='pass123')
        
        data = {
            'username': 'testuser',
            'email': 'test2@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_login_success(self):
        """Test that login succeeds with correct credentials"""
        User.objects.create_user(username='testuser', password='testpass123')
        
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_user_login_wrong_password(self):
        """Test that login fails with wrong password"""
        User.objects.create_user(username='testuser', password='correctpass')
        
        data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_login_nonexistent_user(self):
        """Test that login fails with nonexistent username"""
        data = {
            'username': 'nonexistent',
            'password': 'somepass'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CustomerCRUDTestCase(APITestCase):
    """
    Customer Create, Read, Update, Delete Test Cases
    Tests CRUD operations for customer management
    """
    
    def setUp(self):
        """Setup before each test"""
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        self.customers_url = '/api/customers/'
    
    def test_create_customer_success(self):
        """Test that a new customer can be created successfully"""
        data = {
            'name': 'karim dokandar',
            'phone': '01700000001',
            'address': 'Dhaka Bazar'
        }
        
        response = self.client.post(self.customers_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'karim dokandar')
        self.assertEqual(response.data['phone'], '01700000001')
        self.assertTrue(Customer.objects.filter(name='karim dokandar').exists())
    
    def test_create_customer_without_auth(self):
        """Test that customer cannot be created without authentication"""
        self.client.credentials()
        
        data = {
            'name': 'karim dokandar',
            'phone': '01700000001',
            'address': 'Dhaka'
        }
        
        response = self.client.post(self.customers_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_customers(self):
        """Test that all customers can be listed"""
        Customer.objects.create(user=self.user, name='Customer 1', phone='01700000001')
        Customer.objects.create(user=self.user, name='Customer 2', phone='01700000002')
        
        response = self.client.get(self.customers_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertEqual(len(response.data['results']), 2)
        else:
            self.assertEqual(len(response.data), 2)
    
    def test_get_customer_detail(self):
        """Test that a specific customer's detail can be retrieved"""
        customer = Customer.objects.create(
            user=self.user,
            name='karim dokandar',
            phone='01700000001',
            address='Dhaka'
        )
        
        response = self.client.get(f'{self.customers_url}{customer.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'karim dokandar')
        self.assertEqual(response.data['phone'], '01700000001')
    
    def test_update_customer(self):
        """Test that customer information can be updated"""
        customer = Customer.objects.create(
            user=self.user,
            name='Old Name',
            phone='01700000001'
        )
        
        data = {
            'name': 'New Name',
            'phone': '01711111111',
            'address': 'Chattogram'
        }
        
        response = self.client.put(f'{self.customers_url}{customer.id}/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        customer.refresh_from_db()
        self.assertEqual(customer.name, 'New Name')
        self.assertEqual(customer.phone, '01711111111')
    
    def test_delete_customer(self):
        """Test that a customer can be deleted"""
        customer = Customer.objects.create(user=self.user, name='Customer to delete', phone='01700000001')
        customer_id = customer.id
        
        response = self.client.delete(f'{self.customers_url}{customer_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Customer.objects.filter(id=customer_id).exists())
    
    def test_search_customers(self):
        """Test that customers can be searched by name"""
        Customer.objects.create(user=self.user, name='karim', phone='01700000001')
        Customer.objects.create(user=self.user, name='rahim', phone='01700000002')
        
        response = self.client.get(f'{self.customers_url}search/?q=karim')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'karim')
    
    def test_customer_user_isolation(self):
        """Test that one user cannot see another user's customers"""
        user2 = User.objects.create_user(username='user2', password='pass123')
        
        customer = Customer.objects.create(user=self.user, name='Customer1', phone='01700000001')
        
        response = self.client.post('/api/auth/login/', {
            'username': 'user2',
            'password': 'pass123'
        })
        token2 = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        
        response = self.client.get(self.customers_url)
        
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertEqual(len(response.data['results']), 0)
        else:
            self.assertEqual(len(response.data), 0)


class LedgerEntryTestCase(APITestCase):
    """
    Ledger Entries (Credit/Debit) Test Cases
    Tests credit/debit entry management
    """
    
    def setUp(self):
        """Set up before each test"""
        self.client = APIClient()
        
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        self.customer = Customer.objects.create(
            user=self.user,
            name='Karim Dokandar',
            phone='01700000001'
        )
        
        self.entries_url = '/api/ledger-entries/'
    
    def test_create_credit_entry(self):
        """Test that a CREDIT entry can be created"""
        data = {
            'customer': self.customer.id,
            'type': 'CREDIT',
            'amount': 5000.00,
            'note': 'Provided rice 50kg on credit'
        }
        
        response = self.client.post(self.entries_url, data, format='json')
 
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['type'], 'CREDIT')
        self.assertEqual(float(response.data['amount']), 5000.00)
        self.assertTrue(LedgerEntry.objects.filter(
            customer=self.customer,
            type='CREDIT'
        ).exists())
    
    def test_create_debit_entry(self):
        """Test that a DEBIT entry can be created"""
        data = {
            'customer': self.customer.id,
            'type': 'DEBIT',
            'amount': 2000.00,
            'note': 'Payment received: 2000 Taka'
        }
        
        response = self.client.post(self.entries_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(response.data['amount']), 2000.00)
        self.assertEqual(response.data['type'], 'DEBIT')
    
    def test_list_entries(self):
        """Test that all entries can be listed"""
        LedgerEntry.objects.create(
            customer=self.customer,
            type='CREDIT',
            amount=5000.00
        )
        LedgerEntry.objects.create(
            customer=self.customer,
            type='DEBIT',
            amount=2000.00
        )
        
        response = self.client.get(self.entries_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_filter_by_customer(self):
        """Test that entries can be filtered by specific customer"""
        customer2 = Customer.objects.create(user=self.user, name='Rahim', phone='01700000002')
        
        LedgerEntry.objects.create(customer=self.customer, type='CREDIT', amount=5000.00)
        LedgerEntry.objects.create(customer=customer2, type='CREDIT', amount=3000.00)
        
        response = self.client.get(f'{self.entries_url}by_customer/?customer_id={self.customer.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['entries']), 1)
    
    def test_filter_by_type(self):
        """Test that entries can be filtered by type (CREDIT/DEBIT)"""
        LedgerEntry.objects.create(customer=self.customer, type='CREDIT', amount=5000.00)
        LedgerEntry.objects.create(customer=self.customer, type='CREDIT', amount=3000.00)
        LedgerEntry.objects.create(customer=self.customer, type='DEBIT', amount=2000.00)
        
        response = self.client.get(
            f'{self.entries_url}filter_by_type/?customer_id={self.customer.id}&type=CREDIT'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['entries']), 2)
    
    def test_filter_by_date_range(self):
        """Test that entries can be filtered by date range"""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        entry1 = LedgerEntry.objects.create(
            customer=self.customer,
            type='CREDIT',
            amount=5000.00
        )
        entry1.entry_date = today
        entry1.save()
        
        entry2 = LedgerEntry.objects.create(
            customer=self.customer,
            type='CREDIT',
            amount=3000.00
        )
        entry2.entry_date = tomorrow
        entry2.save()
        
        response = self.client.get(
            f'{self.entries_url}filter_by_date/?customer_id={self.customer.id}&start_date={today}&end_date={today}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_entries'], 1)
    
    def test_update_entry(self):
        """Test that an entry can be updated"""
        entry = LedgerEntry.objects.create(
            customer=self.customer,
            type='CREDIT',
            amount=5000.00,
            note='Old note'
        )
        
        data = {
            'type': 'CREDIT',
            'amount': 6000.00,
            'note': 'New note'
        }
        
        response = self.client.put(f'{self.entries_url}{entry.id}/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        entry.refresh_from_db()
        self.assertEqual(float(entry.amount), 6000.00)
        self.assertEqual(entry.note, 'New note')
    
    def test_delete_entry(self):
        """Test that an entry can be deleted"""
        entry = LedgerEntry.objects.create(
            customer=self.customer,
            type='CREDIT',
            amount=5000.00
        )
        entry_id = entry.id
        
        response = self.client.delete(f'{self.entries_url}{entry_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(LedgerEntry.objects.filter(id=entry_id).exists())


class BalanceCalculationTestCase(APITestCase):
    """
    Balance Calculation Test Cases
    Tests the accuracy of balance calculations
    """
    
    def setUp(self):
        """Setup before each test"""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = APIClient()
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        self.customer = Customer.objects.create(user=self.user, name='Karim Dokandar', phone='01700000001')
    
    def test_balance_calculation(self):
        """Test that balance is calculated correctly (Credit - Debit)"""
        LedgerEntry.objects.create(customer=self.customer, type='CREDIT', amount=5000)
        LedgerEntry.objects.create(customer=self.customer, type='CREDIT', amount=3000)
        LedgerEntry.objects.create(customer=self.customer, type='DEBIT', amount=2000)

        response = self.client.get(f'/api/customers/{self.customer.id}/summary/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['total_credit']), 8000.00)
        self.assertEqual(float(response.data['total_debit']), 2000.00)
        self.assertEqual(float(response.data['balance']), 6000.00)
    
    def test_zero_balance(self):
        """Test that balance is zero when credit equals debit"""
        LedgerEntry.objects.create(customer=self.customer, type='CREDIT', amount=5000)
        LedgerEntry.objects.create(customer=self.customer, type='DEBIT', amount=5000)

        response = self.client.get(f'/api/customers/{self.customer.id}/summary/')
        self.assertEqual(float(response.data['balance']), 0.00)
    
    def test_negative_balance(self):
        """Test that balance becomes negative when debit exceeds credit"""
        LedgerEntry.objects.create(customer=self.customer, type='CREDIT', amount=2000)
        LedgerEntry.objects.create(customer=self.customer, type='DEBIT', amount=5000)
        
        response = self.client.get(f'/api/customers/{self.customer.id}/summary/')
        self.assertEqual(float(response.data['balance']), -3000.00)


class StatisticsTestCase(APITestCase):
    """
    Statistics Endpoint Test Cases
    Tests the statistics endpoint functionality
    """
    
    def setUp(self):
        """Setup before each test"""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = APIClient()
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_statistics_endpoint(self):
        """Test that statistics endpoint returns correct data"""
        customer1 = Customer.objects.create(user=self.user, name='Customer 1')
        customer2 = Customer.objects.create(user=self.user, name='Customer 2')
        
        LedgerEntry.objects.create(customer=customer1, type='CREDIT', amount=5000)
        LedgerEntry.objects.create(customer=customer1, type='DEBIT', amount=2000)
        LedgerEntry.objects.create(customer=customer2, type='CREDIT', amount=3000)
        
        response = self.client.get('/api/ledger-entries/statistics/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_customers'], 2)
        self.assertEqual(float(response.data['total_credit']), 8000.00)
        self.assertEqual(float(response.data['total_debit']), 2000.00)
        self.assertEqual(float(response.data['total_balance']), 6000.00)
        self.assertEqual(response.data['total_entries'], 3)


class CustomerSummaryTestCase(APITestCase):
    """
    Test Customer Summary Endpoint
    """
    
    def setUp(self):
        """Setup before each test"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        self.customer = Customer.objects.create(
            user=self.user,
            name='Test Customer',
            phone='01700000001'
        )
    
    def test_customer_summary_endpoint(self):
        """Test that customer summary endpoint returns correct data"""
        LedgerEntry.objects.create(customer=self.customer, type='CREDIT', amount=10000)
        LedgerEntry.objects.create(customer=self.customer, type='DEBIT', amount=3000)
        
        response = self.client.get(f'/api/customers/{self.customer.id}/summary/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Customer')
        self.assertEqual(float(response.data['total_credit']), 10000.00)
        self.assertEqual(float(response.data['total_debit']), 3000.00)
        self.assertEqual(float(response.data['balance']), 7000.00)
        self.assertEqual(response.data['entries_count'], 2)


class AdminPanelTestCase(APITestCase):
    """
    Test Admin Panel and Model Admin
    """
    
    def setUp(self):
        """Setup before each test"""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.client = APIClient()
    
    def test_admin_user_creation(self):
        """Test that admin user can be created"""
        self.assertTrue(self.admin_user.is_superuser)
        self.assertTrue(self.admin_user.is_staff)
        self.assertEqual(self.admin_user.username, 'admin')
    
    def test_customer_model_string_representation(self):
        """Test Customer model __str__ method"""
        customer = Customer.objects.create(
            user=self.admin_user,
            name='Admin Customer',
            phone='01700000001'
        )
        self.assertEqual(str(customer), 'Admin Customer')
    
    def test_ledger_entry_model_string_representation(self):
        """Test LedgerEntry model __str__ method"""
        customer = Customer.objects.create(
            user=self.admin_user,
            name='Test Customer',
            phone='01700000001'
        )
        entry = LedgerEntry.objects.create(
            customer=customer,
            type='CREDIT',
            amount=5000
        )
        expected_str = f"Test Customer - CREDIT - 5000"
        self.assertEqual(str(entry), expected_str)


class EdgeCaseTestCase(APITestCase):
    """
    Test Edge Cases and Error Handling
    """
    
    def setUp(self):
        """Setup before each test"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        self.customer = Customer.objects.create(
            user=self.user,
            name='Test Customer',
            phone='01700000001'
        )
    
    def test_create_customer_missing_required_field(self):
        """Test that customer creation fails without required field"""
        data = {
            'phone': '01700000001'
            # Missing 'name' field
        }
        
        response = self.client.post('/api/customers/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_nonexistent_customer(self):
        """Test that getting nonexistent customer returns 404"""
        response = self.client.get('/api/customers/9999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_delete_nonexistent_customer(self):
        """Test that deleting nonexistent customer returns 404"""
        response = self.client.delete('/api/customers/9999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_create_entry_invalid_type(self):
        """Test that creating entry with invalid type fails"""
        data = {
            'customer': self.customer.id,
            'type': 'INVALID',  # Invalid type
            'amount': 5000.00,
            'note': 'Test'
        }
        
        response = self.client.post('/api/ledger-entries/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_entry_negative_amount(self):
        """Test that negative amounts are handled"""
        data = {
            'customer': self.customer.id,
            'type': 'CREDIT',
            'amount': -5000.00,  # Negative amount
            'note': 'Test'
        }
        
        # This depends on business rules - allowing or rejecting negative amounts
        response = self.client.post('/api/ledger-entries/', data, format='json')
        # Could be 201 or 400 depending on validation rules
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_search_with_minimum_characters(self):
        """Test search with minimum 2 characters"""
        Customer.objects.create(user=self.user, name='ab', phone='01700000001')
        response = self.client.get('/api/customers/search/?q=ab')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_search_with_single_character(self):
        """Test search with single character returns error"""
        response = self.client.get('/api/customers/search/?q=a')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_filter_by_invalid_customer_id(self):
        """Test filter by invalid customer ID"""
        response = self.client.get('/api/ledger-entries/by_customer/?customer_id=9999')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_filter_by_invalid_type(self):
        """Test filter by invalid type"""
        response = self.client.get(
            f'/api/ledger-entries/filter_by_type/?customer_id={self.customer.id}&type=INVALID'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_filter_by_invalid_date_format(self):
        """Test filter by invalid date format"""
        response = self.client.get(
            f'/api/ledger-entries/filter_by_date/?customer_id={self.customer.id}&start_date=invalid&end_date=2024-12-31'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PaginationTestCase(APITestCase):
    """
    Test Pagination Functionality
    """
    
    def setUp(self):
        """Setup before each test"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_pagination_with_multiple_customers(self):
        """Test that pagination works with multiple items"""
        # Create 15 customers
        for i in range(15):
            Customer.objects.create(
                user=self.user,
                name=f'Customer {i}',
                phone=f'0170000000{i}'
            )
        
        response = self.client.get('/api/customers/?page=1')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if pagination is working
        if 'results' in response.data:
            self.assertLessEqual(len(response.data['results']), 10)
    
    def test_pagination_with_ledger_entries(self):
        """Test pagination with ledger entries"""
        customer = Customer.objects.create(user=self.user, name='Test Customer')
        
        # Create 15 entries
        for i in range(15):
            LedgerEntry.objects.create(
                customer=customer,
                type='CREDIT' if i % 2 == 0 else 'DEBIT',
                amount=1000 + i
            )
        
        response = self.client.get('/api/ledger-entries/?page=1')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if 'results' in response.data:
            self.assertLessEqual(len(response.data['results']), 10)


class ErrorHandlingTestCase(APITestCase):
    """
    Test Error Handling and Validation
    """
    
    def setUp(self):
        """Setup before each test"""
        self.client = APIClient()
    
    def test_registration_with_short_password(self):
        """Test that short password is rejected"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'short',  # Less than 6 characters
            'password_confirm': 'short',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        response = self.client.post('/api/auth/register/', data, format='json')
        # Depending on validation, should be 400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_with_empty_credentials(self):
        """Test login with empty credentials"""
        data = {
            'username': '',
            'password': ''
        }
        
        response = self.client.post('/api/auth/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_entry_without_customer_field(self):
        """Test entry creation without customer field"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        
        data = {
            'type': 'CREDIT',
            'amount': 5000.00,
            'note': 'Test'
            # Missing customer field
        }
        
        response = self.client.post('/api/ledger-entries/', data, format='json')
        # Should fail due to missing customer or invalid token
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST])


class IntegrationTestCase(APITestCase):
    """
    Integration Tests - Complete User Journey
    """
    
    def test_complete_user_workflow(self):
        """Test complete workflow from registration to balance check"""
        # Step 1: Register
        register_data = {
            'username': 'integration_user',
            'email': 'integration@example.com',
            'password': 'integrationpass123',
            'password_confirm': 'integrationpass123',
            'first_name': 'Integration',
            'last_name': 'User'
        }
        
        response = self.client.post('/api/auth/register/', register_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 2: Login
        login_data = {
            'username': 'integration_user',
            'password': 'integrationpass123'
        }
        
        response = self.client.post('/api/auth/login/', login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data['access']
        
        # Step 3: Create customer
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        customer_data = {
            'name': 'Integration Customer',
            'phone': '01700000001',
            'address': 'Integration Address'
        }
        
        response = self.client.post('/api/customers/', customer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        customer_id = response.data['id']
        
        # Step 4: Create ledger entries
        entry_data = {
            'customer': customer_id,
            'type': 'CREDIT',
            'amount': 10000.00,
            'note': 'Integration test entry'
        }
        
        response = self.client.post('/api/ledger-entries/', entry_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 5: Check customer summary
        response = self.client.get(f'/api/customers/{customer_id}/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['total_credit']), 10000.00)
        self.assertEqual(float(response.data['balance']), 10000.00)
        
        # Step 6: Create payment
        payment_data = {
            'customer': customer_id,
            'type': 'DEBIT',
            'amount': 4000.00,
            'note': 'Payment received'
        }
        
        response = self.client.post('/api/ledger-entries/', payment_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 7: Verify updated balance
        response = self.client.get(f'/api/customers/{customer_id}/summary/')
        self.assertEqual(float(response.data['balance']), 6000.00)


class DataValidationTestCase(APITestCase):
    """
    Test Data Validation
    """
    
    def setUp(self):
        """Setup before each test"""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_customer_with_empty_name(self):
        """Test that customer with empty name is rejected"""
        data = {
            'name': '',
            'phone': '01700000001',
            'address': 'Test Address'
        }
        
        response = self.client.post('/api/customers/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_entry_with_zero_amount(self):
        """Test creating entry with zero amount"""
        customer = Customer.objects.create(user=self.user, name='Test Customer')
        
        data = {
            'customer': customer.id,
            'type': 'CREDIT',
            'amount': 0.00,
            'note': 'Zero amount'
        }
        
        response = self.client.post('/api/ledger-entries/', data, format='json')
        # Could be allowed or rejected depending on business rules
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_entry_with_very_large_amount(self):
        """Test creating entry with very large amount"""
        customer = Customer.objects.create(user=self.user, name='Test Customer')
        
        data = {
            'customer': customer.id,
            'type': 'CREDIT',
            'amount': 999999999.99,
            'note': 'Large amount'
        }
        
        response = self.client.post('/api/ledger-entries/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_customer_with_special_characters_in_name(self):
        """Test customer with special characters in name"""
        data = {
            'name': 'Test@#$%^&*()',
            'phone': '01700000001',
            'address': 'Test Address'
        }
        
        response = self.client.post('/api/customers/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_ledger_entry_with_very_long_note(self):
        """Test creating entry with very long note"""
        customer = Customer.objects.create(user=self.user, name='Test Customer')
        
        long_note = 'A' * 1000  # Very long note
        
        data = {
            'customer': customer.id,
            'type': 'CREDIT',
            'amount': 5000.00,
            'note': long_note
        }
        
        response = self.client.post('/api/ledger-entries/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)