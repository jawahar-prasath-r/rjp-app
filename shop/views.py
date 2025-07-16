from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Order
from .payment_utils import PaymentProcessor, OfflinePaymentHandler
import csv
import json

def home(request):
    # Get product choices from the model to ensure consistency
    from .models import Order
    products = [choice[0] for choice in Order.PRODUCT_CHOICES]
    return render(request, 'shop/home.html', {'products': products})

def products(request):
    """Products page with detailed information"""
    from .models import Order

    # Product information with prices
    products_info = [
        {
            'name': 'motha kendai',
            'display_name': 'Motha Kendai',
            'tamil_name': 'மொத்த கெண்டை',
            'price': Order.PRODUCT_PRICES.get('motha kendai', 450),
            'icon': '🐟',
            'description': 'Firm, thick-fleshed dry fish known for its intense flavor and chewy texture.',
        },
        {
            'name': 'netthili',
            'display_name': 'Netthili',
            'tamil_name': 'நெத்திலி Dry Fish / Anchovy',
            'price': Order.PRODUCT_PRICES.get('netthili', 400),
            'icon': '🐟',
            'description': 'Small, slender dry fish widely loved in South India with salty-sweet flavor.',
        },
        {
            'name': 'vaalai',
            'display_name': 'Vaalai',
            'tamil_name': 'வாளை Dry Fish',
            'price': Order.PRODUCT_PRICES.get('vaalai', 300),
            'icon': '🐟',
            'description': 'Medium-sized dry fish with soft flesh and mild aroma, perfect for gravies.',
        },
        {
            'name': 'goa netthili',
            'display_name': 'Goa Netthili',
            'tamil_name': 'Goan Anchovy Dry Fish',
            'price': Order.PRODUCT_PRICES.get('goa netthili', 600),
            'icon': '🐟',
            'description': 'Coastal variation of netthili, larger and saltier with crispy texture.',
        },
        {
            'name': 'yeera',
            'display_name': 'Yeera',
            'tamil_name': 'Dry Shrimp / உலர்ந்த இறால்',
            'price': Order.PRODUCT_PRICES.get('yeera', 500),
            'icon': '🦐',
            'description': 'Dried shrimp, one of the most flavor-rich seafood ingredients.',
        },
    ]

    return render(request, 'shop/products.html', {'products_info': products_info})

@login_required
def order(request):
    # Pre-fill user information if available
    user_data = {}
    if request.user.is_authenticated:
        user_data = {
            'name': request.user.get_full_name() or request.user.first_name,
            'email': request.user.email,
        }

    # Get pre-selected product from URL parameter
    pre_selected_product = request.GET.get('product', '')

    if request.method == 'POST':
        try:
            # Validate required fields
            name = request.POST.get('name', '').strip()
            mobile = request.POST.get('mobile', '').strip()
            address = request.POST.get('address', '').strip()
            product = request.POST.get('product', '').strip()
            quantity_str = request.POST.get('quantity', '').strip()

            # Preserve form data for re-rendering
            form_data = {
                'name': name,
                'mobile': mobile,
                'address': address,
                'product': product,
                'quantity': quantity_str,
            }

            # Check if all fields are provided
            if not all([name, mobile, address, product, quantity_str]):
                messages.error(request, 'Please fill all required fields.')
                return render(request, 'shop/order.html', {'user_data': user_data, 'form_data': form_data})

            # Validate quantity
            try:
                quantity = float(quantity_str)
                if quantity <= 0:
                    messages.error(request, 'Quantity must be greater than 0.')
                    return render(request, 'shop/order.html', {'user_data': user_data, 'form_data': form_data})
            except ValueError:
                messages.error(request, 'Please enter a valid quantity.')
                return render(request, 'shop/order.html', {'user_data': user_data, 'form_data': form_data})

            # Validate product choice
            valid_products = [choice[0] for choice in Order.PRODUCT_CHOICES]
            if product not in valid_products:
                messages.error(request, 'Please select a valid product.')
                return render(request, 'shop/order.html', {'user_data': user_data, 'form_data': form_data})

            # Create order without payment initially
            new_order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                name=name,
                mobile=mobile,
                address=address,
                product=product,
                quantity=quantity,
                payment_status='pending'
            )

            messages.success(request, f'Order #{new_order.id} created successfully! Please complete payment.')
            # Redirect to payment page
            return redirect('payment', order_id=new_order.id)

        except Exception as e:
            messages.error(request, f'Error creating order: {str(e)}. Please try again.')
            form_data = request.POST.dict()
            return render(request, 'shop/order.html', {'user_data': user_data, 'form_data': form_data})

    return render(request, 'shop/order.html', {'user_data': user_data})

@login_required
def payment(request, order_id):
    """Payment selection and processing page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        order.payment_method = payment_method

        if payment_method in ['cash_on_delivery', 'bank_transfer']:
            # Handle offline payments
            OfflinePaymentHandler.process_offline_payment(order, payment_method)
            return redirect('payment_confirmation', order_id=order.id)
        else:
            # Handle online payments
            order.transaction_id = PaymentProcessor.generate_transaction_id()
            order.save()
            return redirect('payment_process', order_id=order.id)

    return render(request, 'shop/payment.html', {'order': order})

@login_required
def payment_process(request, order_id):
    """Process online payments"""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.payment_method == 'google_pay':
        # Google Pay app redirect
        google_pay_url = PaymentProcessor.get_google_pay_url(order)
        context = {
            'order': order,
            'app_url': google_pay_url,
            'app_name': 'Google Pay',
            'app_icon': 'fab fa-google-pay',
            'fallback_url': PaymentProcessor.get_upi_payment_url(order),
            'payment_method': 'google_pay'
        }
        return render(request, 'shop/app_payment_redirect.html', context)

    elif order.payment_method == 'phonepe':
        # PhonePe app redirect
        phonepe_url = PaymentProcessor.get_phonepe_url(order)
        context = {
            'order': order,
            'app_url': phonepe_url,
            'app_name': 'PhonePe',
            'app_icon': 'fas fa-mobile-alt',
            'fallback_url': PaymentProcessor.get_upi_payment_url(order),
            'payment_method': 'phonepe'
        }
        return render(request, 'shop/app_payment_redirect.html', context)

    elif order.payment_method == 'paytm':
        # Paytm app redirect
        paytm_url = PaymentProcessor.get_paytm_url(order)
        context = {
            'order': order,
            'app_url': paytm_url,
            'app_name': 'Paytm',
            'app_icon': 'fas fa-wallet',
            'fallback_url': PaymentProcessor.get_upi_payment_url(order),
            'payment_method': 'paytm'
        }
        return render(request, 'shop/app_payment_redirect.html', context)

    elif order.payment_method == 'upi':
        # UPI payment
        upi_url = PaymentProcessor.get_upi_payment_url(order)
        context = {
            'order': order,
            'upi_url': upi_url
        }
        return render(request, 'shop/upi_payment.html', context)

    else:
        # Fallback for other payment methods
        messages.error(request, 'Payment method not supported')
        return redirect('payment', order_id=order.id)

@login_required
def payment_confirmation(request, order_id):
    """Payment confirmation page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    context = {
        'order': order,
        'bank_details': OfflinePaymentHandler.get_bank_details() if order.payment_method == 'bank_transfer' else None,
        'cod_info': OfflinePaymentHandler.get_cod_instructions() if order.payment_method == 'cash_on_delivery' else None
    }

    return render(request, 'shop/payment_confirmation.html', context)

@csrf_exempt
@login_required
def payment_verify(request):
    """Verify Razorpay payment"""
    if request.method == 'POST':
        try:
            payment_id = request.POST.get('razorpay_payment_id')
            order_id = request.POST.get('razorpay_order_id')
            signature = request.POST.get('razorpay_signature')

            # Verify payment signature
            if PaymentProcessor.verify_razorpay_payment(payment_id, order_id, signature):
                # Find order by transaction_id (which is the razorpay_order_id)
                order = Order.objects.get(transaction_id=order_id, user=request.user)

                # Mark payment as completed
                order.payment_status = 'completed'
                order.paid = True
                order.save()

                messages.success(request, f'Payment successful! Order #{order.id} has been confirmed and is being processed.')
                return JsonResponse({'status': 'success', 'redirect_url': '/orders/'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Payment verification failed'})

        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Order not found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def payment_success(request, order_id):
    """Payment success callback - redirect to view orders"""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Mark payment as completed
    order.payment_status = 'completed'
    order.paid = True
    order.save()

    messages.success(request, f'Payment successful! Order #{order.id} has been confirmed and is being processed.')
    return redirect('view_orders')

@login_required
def view_orders(request):
    """View user's orders with beautiful UI"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/view_orders.html', {'orders': orders})

@login_required
def export_orders(request):
    if not request.user.is_authenticated:
        return redirect('home')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'
    writer = csv.writer(response)
    writer.writerow(['Name', 'Mobile', 'Address', 'Product', 'Quantity', 'Payment Method', 'Payment Status', 'Total Amount', 'Paid'])
    for order in Order.objects.filter(user=request.user):
        writer.writerow([
            order.name, order.mobile, order.address, order.product,
            order.quantity, order.get_payment_method_display(),
            order.get_payment_status_display(), order.total_amount, order.paid
        ])
    return response

def login_view(request):
    """Manual login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Successfully logged in!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'registration/login.html')

def signup_view(request):
    """Manual signup view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('account_login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})

def logout_view(request):
    """Custom logout view with confirmation"""
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been successfully logged out!')
        return redirect('home')

    return render(request, 'registration/logout.html')
