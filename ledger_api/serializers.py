from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Customer, LedgerEntry
from django.contrib.auth import authenticate


class UserRegistrationSerializer(serializers.ModelSerializer):
    #  For User registration
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']

    def validate(self, data):
        # Check if both passwords match
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password': 'passwords do not match'})
        return data

    def create(self, validated_data):
        # Create a new user
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    #  For User login
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        # Validate username and password
        user = authenticate(
            username=data.get('username'),
            password=data.get('password')
        )
        if not user:
            raise serializers.ValidationError('Invalid username or password')
        data['user'] = user
        return data


class CustomerSerializer(serializers.ModelSerializer):
    #  For creating, updating, and viewing Customer details
    
    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone', 'address', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class LedgerEntrySerializer(serializers.ModelSerializer):
    #  For creating and viewing Ledger entries
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = LedgerEntry
        fields = ['id', 'type', 'type_display', 'amount', 'note', 'entry_date', 'created_at']
        read_only_fields = ['id', 'created_at', 'entry_date']


class CustomerSummarySerializer(serializers.ModelSerializer):
    #  For viewing Customer summary details
    total_credit = serializers.SerializerMethodField()
    total_debit = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    entries_count = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'phone', 'address', 
            'total_credit', 'total_debit', 'balance', 
            'entries_count', 'created_at'
        ]
        read_only_fields = fields

    def get_total_credit(self, obj):
        summary = obj.get_summary()
        return summary['total_credit']

    def get_total_debit(self, obj):
        summary = obj.get_summary()
        return summary['total_debit']

    def get_balance(self, obj):
        summary = obj.get_summary()
        return summary['balance']

    def get_entries_count(self, obj):
        return obj.ledger_entries.count()