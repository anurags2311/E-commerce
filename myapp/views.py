from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.shortcuts import render, get_object_or_404, redirect
import stripe
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from django.views.decorators.http import require_POST
from django.conf import settings
from myapp.models import *
from twilio.rest import Client
from django.core.mail import send_mail
import uuid as uuid
# from decouple import config
from django.core.paginator import Paginator
import  random








class RegisterForm(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        name = request.POST['name']
        username = request.POST['username']
        email = request.POST['email']
        phone = request.POST['phone']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            return HttpResponse("Passwords do not match")

        subject = 'Verify Your Email'
        token = str(uuid.uuid4())  # Generate a UUID token
        link = f"http://127.0.0.1:8000/verify/?token={token}"  
        message = f'Click the link below to verify your email: {link}'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email]

        send_mail(subject, message, email_from, recipient_list, fail_silently=False)
        email_verify.objects.create(email=email, token=token)

        user = User(
            name=name,
            username=username,
            email=email,
            phone=phone,
            password=make_password(password1)
        )
        user.save()

        return render(request, 'verify_email.html')
    
    

class LoginForm(View):
    def get(self, request):
        user = request.user
        return render(request, 'login.html', {"user": user})

    def post(self, request):
      


        if request.method == 'POST':
            email = request.POST.get('username')  
            password = request.POST.get('password')
           

            user = authenticate(request, email=email, password=password) 

            if user is not None:
                login(request, user) 
                return redirect(f'/home/?user={user.id}')
            else:
                return HttpResponse("Invalid credentials")
            
    


class HomePage(View):
    def get(self, request):
        # Ensure the user is authenticated
        if not request.user.is_authenticated:
            return HttpResponse("Invalid User")

        # Fetch products and shuffle them
        products = Products.objects.all()
        products = list(products)  # Convert QuerySet to a list
        random.shuffle(products)  # Shuffle the list of products

        # Paginate products
        paginator = Paginator(products, 30)  # Show 10 products per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Return rendered page with products
        return render(request, 'home.html', {'products': page_obj, 'user': request.user})

class DetailPage(View):
    def get(self, request, id, *args, **kwargs):
        userid=request.GET.get('user')
        
        product=Products.objects.filter(id=id).last()
        products=Products.objects.filter(category_id=product.category_id).exclude(id=product.id)
        products= list(products)  # Convert QuerySet to a list
        random.shuffle(products)
        related_products = products[:4]  # Get 4 related products
    
        
        return render(request, 'detailpage.html',{
            'product': product,
            'related_products': related_products,
            'user': request.user
        })
    

 


class CartView(View):
    def get(self, request, id):
       
        user_id = request.GET.get('user')
        user = User.objects.filter(id=user_id).last()
        product = get_object_or_404(Products, id=id)
        
        if not user:
            return JsonResponse({"status": "error", "message": "User not found!"})

        
        check = Cart.objects.filter(Products=product, user=user.id).last()
        if check:
            return JsonResponse({"status": "warning", "message": "Item already in cart!"})

        
        Cart.objects.create(
            Products=product,
            user=user,
            quantity=1,
            total_amount=product.price,
            image=product.image
        )

        return JsonResponse({"status": "success", "message": "Item added to cart successfully!"})
    
class Remove_cart(View):
    def get(self, request, id):
        user_id = request.user.id 
        user = User.objects.filter(id=user_id).last()
        product = Products.objects.filter(id=id).last()
        if product:
            cart_item = Cart.objects.filter(Products=product.id, user=user).last()
            if cart_item:
                cart_item.delete()  
                return JsonResponse({"status": "success", "message": "Item removed from cart successfully!"})
            else:
                return JsonResponse({"status": "error", "message": "Item not found in cart."})
        else:
            return JsonResponse({"status": "error", "message": "Product does not exist."})

class CartPageView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return HttpResponse("User not authenticated!", status=401)

        user = request.user

        # Fetch cart items for the user
        cart_items = Cart.objects.filter(user=user)
        
        total_amount = sum(item.total_amount for item in cart_items)
        

        # Render the cart page
        return render(request, 'cart.html', {
            'cart_items': cart_items,
            'total_amount': total_amount,
            'user': user
            
        })


class AddItem(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return HttpResponse("User not authenticated!", status=401)

        user = request.user

        # Fetch cart items for the user
        data = Cart.objects.filter(user=user).all()
        total_amount = sum(item.total_amount for item in data)

        return render(request, "bag.html", {"data": data, "price": total_amount, "user": user})
    

class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request) 
        return redirect('login')  
    

class MyOrdersView(View):
    def get(self, request):
        user_id = request.GET.get('user')
        user = User.objects.filter(id=user_id).first()
       
        if not user:
            return HttpResponse("Invalid User")

        
        transactions = Transaction.objects.filter(user_id=user).order_by('-created_at')

        
        orders = []
        for transaction in transactions:
            cart_items = transaction.items.all()  
            orders.append({
                'transaction': transaction,
                'cart_items': cart_items,
                
            })

        return render(request, 'myorders.html', {'orders': orders, 'user': user_id})





#//////////////// payment gateway///////////////

stripe.api_key = "sk_test_51R10aqBSTAAEIUsJkuRi05oBcyiTBtoTyUjikxCV9kPJDPNTSK5pGnz7A0G3jRvPEASnDOaO7wLBiQebTgUak8ed00IsG8YMpv"
@csrf_exempt
def create_checkout_session(request):
    user_id = request.GET.get('user')
    user = User.objects.filter(id=user_id).last()

    if request.method == "POST":
        try:
            data = json.loads(request.body)  
            cart_total_inr = float(data.get("cart_total", 0))  

           
            response = requests.get('https://api.exchangerate-api.com/v4/latest/INR')
            exchange_rate = response.json().get('rates', {}).get('USD', 0.012)  

            if not exchange_rate:
                return JsonResponse({'error': 'Unable to fetch exchange rate'}, status=500)

           
            cart_total_usd = round(cart_total_inr * exchange_rate, 2)  
            cart_total_usd_cents = int(cart_total_usd * 100)  

            print(f"Cart Total INR: {cart_total_inr}, Converted USD: {cart_total_usd}, Cents: {cart_total_usd_cents}")

           
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                customer_email=user.email,  
                line_items=[{
                    'price_data': {
                        'currency': 'USD',
                        'product_data': {'name': 'Shopping Cart Items'},
                        'unit_amount': cart_total_usd_cents,  
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url='http://127.0.0.1:8000/success',
                cancel_url='http://127.0.0.1:8000/cancel',
            )

            return JsonResponse({'id': session.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

           

            return JsonResponse({'id': session.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError as e:
        return JsonResponse({'error': f'Invalid payload: {str(e)}'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        return JsonResponse({'error': f'Invalid signature: {str(e)}'}, status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        email = session.get("customer_details", {}).get("email", None)

        if email:
            user = User.objects.filter(email=email).first()

            if user:
                cart_items = Cart.objects.filter(user=user)
                if cart_items.exists():
                    cart_instance = cart_items.first()  
                    print(f"Cart instance being passed: {cart_instance}, ID: {cart_instance.id}")

                    transaction = Transaction(
                        user=user,
                        total_amount=session.get("amount_total", 0) / 100,
                        transaction_id=session.get("id", "")
                    )
                    transaction.save()
                   

                    for cart_item in cart_items:
                        item = TransactionCartItem.objects.create(
                            transaction=transaction,
                            product=cart_item.Products,
                            quantity=cart_item.quantity,
                            total_price=cart_item.total_amount
                        )
                        print(f"Created TransactionCartItem: {item.id}")

                        cart_items.delete()  
                        print("Cleared cart items but kept the cart instance")

                    print(f"Transaction {transaction.id} created successfully with cart items!")
                else:
                    print("No cart items found for the user.")
            else:
                print("User not found.")
        else:
            print("Email not found in the session.")

    return JsonResponse({'message': 'Event received'}, status=200)


def payment_success(request):
    return render (request , "success.html")


def payment_cancel(request):
    return render(request, "cancel.html")






class WishlistView(View):
    def get(self, request):
        user_id = request.GET.get('user')
        id= request.user.id
       
        wishlist_items = WishlistItem.objects.filter(user=id).all()
        wish_list= []
        for i in wishlist_items:
            data={ 
                "id":i.id,
                "user":i.user,
                "image":i.image,
                "product":i.product,
                "created_at":i.created_at
             }
        
            wish_list.append(data)
      
        return render(request, 'wishlist.html', {'wishlist_items': wish_list})
    


class RemoveFromWishlistView(View):
    def post(self, request, item_id):
        wishlist_item = get_object_or_404(WishlistItem, id=item_id)
        wishlist_item.delete()
        return JsonResponse({"status": "success", "message": "Item removed from wishlist successfully!"})


class MoveToCartView(View):
    def post(self, request, item_id):
        wishlist_item = get_object_or_404(WishlistItem, id=item_id)
        Cart.objects.create(
            user=wishlist_item.user,
            Products=wishlist_item.product,
            quantity=1,
            total_amount=wishlist_item.product.price,
            image=wishlist_item.product.image
        )
        wishlist_item.delete()
        return JsonResponse({"status": "success", "message": "Item moved to cart successfully!"})



class AddToWishlistView(View):
    def get(self, request, product_id):
        user_id = request.GET.get('user')
        user = User.objects.filter(id=user_id).first()
        product = get_object_or_404(Products, id=product_id)

        if not user:
            return JsonResponse({"status": "error", "message": "User not found!"})

        
        existing_item = WishlistItem.objects.filter(user=user, product=product).first()
        if existing_item:
            return JsonResponse({"status": "warning", "message": "Item already in wishlist!"})

        
        WishlistItem.objects.create(user=user, product=product, image=product.image)
        return JsonResponse({"status": "success", "message": "Item added to wishlist successfully!"})


class ProfileView(View):
    def get(self, request):
        user = request.user
        return render(request, 'my_profile.html', {'user': user})


class VerifyPhoneView(View):
    def get(self, request):
        token = request.GET.get('token')
        user = get_object_or_404(User, id=token)

        if not user.phone_verified:
            # Initialize Twilio client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            otp= str(uuid.uuid4())[:6]  # Generate a random OTP
            print(otp)
            # Send verification code to the user's phone number
            verification = client.verify.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
                to=user.phone,  # Ensure the phone number is in E.164 format (e.g., +1234567890)
                channel='sms',  # You can also use 'call' for voice verification
                custom_code=otp  # Use the generated OTP as the verification code
            )

            return JsonResponse({"status": "success", "message": "Verification code sent to your phone!"})
        else:
            return JsonResponse({"status": "error", "message": "Phone number is already verified!"})

    def post(self, request):
        token = request.GET.get('token')
        user = get_object_or_404(User, id=token)

        if not user.phone_verified:
            # Get the verification code from the request
            verification_code = request.POST.get('verification_code')

            # Initialize Twilio client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

            # Verify the code
            verification_check = client.verify.services(settings.TWILIO_VERIFY_SERVICE_SID).verification_checks.create(
                to=user.phone,
                code=verification_code
            )

            if verification_check.status == 'approved':
                user.phone_verified = True
                user.save()
                return JsonResponse({"status": "success", "message": "Phone number verified successfully!"})
            else:
                return JsonResponse({"status": "error", "message": "Invalid verification code!"})
        else:
            return JsonResponse({"status": "error", "message": "Phone number is already verified!"})


class SendOTPView(View):
    def get(self, request):
        token = request.GET.get('token')
        user = get_object_or_404(User, id=token)

        if not user.phone_verified:
            # Ensure the phone number is in E.164 format
            phone_number = user.phone
            if not phone_number.startswith('+'):
                phone_number = f"+91{phone_number}"  # Assuming the country code is +91 (India)

            # Initialize Twilio client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

            try:
                # Send OTP to the user's phone number
                verification = client.verify.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
                    to=phone_number,
                    channel='sms'
                )
                return JsonResponse({"status": "success", "message": "OTP sent to your phone!"})
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)})
        else:
            return JsonResponse({"status": "error", "message": "Phone number is already verified!"})




class SearchProductsView(View):
    def get(self, request):
        query = request.GET.get('query', '')
        products = Products.objects.filter(name__icontains=query)
        # products = Products.objects.filter(id=id)
        products = list(products)  # Convert QuerySet to a list
        random.shuffle(products)  # Shuffle the list of products

        # Paginate products
        paginator = Paginator(products, 30)  # Show 10 products per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)  # Search by product name
        return render(request, 'search_results.html', {'products': page_obj, 'query':query})





class MenView(View):
    def get(self, request):
        # Fetch men's products
        products = Products.objects.filter(category_id__in=[1, 2, 3])
        products = list(products)  # Convert QuerySet to a list
        random.shuffle(products)  # Shuffle the list of products

        # Paginate products
        paginator = Paginator(products, 30)  # Show 10 products per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'men.html', {'products': page_obj, 'user': request.user})




class MenShirtsView(View):
    def get(self, request):
        # Fetch men's products
        products = Products.objects.filter(category_id='1')
        products = list(products)  # Convert QuerySet to a list
        random.shuffle(products)  # Shuffle the list of products

        # Paginate products
        paginator = Paginator(products, 30)  # Show 10 products per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)  # Adjust the category IDs as needed
        return render(request, 'men_shirts.html', {'products': page_obj, 'user': request.user})

    
class MenPoloView(View):
    def get(self, request):
        # Fetch men's products
        products = Products.objects.filter(category_id='2')
        products = list(products)  # Convert QuerySet to a list
        random.shuffle(products)  # Shuffle the list of products

        # Paginate products
        paginator = Paginator(products, 30)  # Show 10 products per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)  # Adjust the category IDs as needed
        return render(request, 'men_polos.html', {'products': page_obj, 'user': request.user})


class MenBottomwearView(View):
    def get(self, request):
        # Fetch men's products
        products = Products.objects.filter(category_id='3')
        products = list(products)  # Convert QuerySet to a list
        random.shuffle(products)  # Shuffle the list of products

        # Paginate products
        paginator = Paginator(products, 30)  # Show 10 products per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)  # Adjust the category IDs as needed
        return render(request, 'men_bottomwear.html', {'products': page_obj, 'user': request.user})

class WomenView(View):
    def get(self, request):
        # Fetch men's products
        products = Products.objects.filter(category_id__in=[ 4, 5])
        products = list(products)  # Convert QuerySet to a list
        random.shuffle(products)  # Shuffle the list of products

        # Paginate products
        paginator = Paginator(products, 30)  # Show 10 products per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)  # Adjust the category IDs as needed
        return render(request, 'women.html', {'products': page_obj, 'user': request.user})

class WomenTopwearView(View):
    def get(self, request):
        # Fetch men's products
        products = Products.objects.filter(category_id='4')
        products = list(products)  # Convert QuerySet to a list
        random.shuffle(products)  # Shuffle the list of products

        # Paginate products
        paginator = Paginator(products, 30)  # Show 10 products per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)  # Adjust the category IDs as needed
        return render(request, 'women_topwear.html', {'products': page_obj, 'user': request.user})

class WomenBottomwearView(View):
    def get(self, request):
        # Fetch men's products
        products = Products.objects.filter(category_id='5')
        products = list(products)  # Convert QuerySet to a list
        random.shuffle(products)  # Shuffle the list of products

        # Paginate products
        paginator = Paginator(products, 30)  # Show 10 products per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)  # Adjust the category IDs as needed
        return render(request, 'women_bottomwear.html', {'products': page_obj, 'user': request.user})

class AccessoriesView(View):
    def get(self, request):
        # Fetch men's products
        products = Products.objects.filter(category_id__in=[ 6, 7])
        products = list(products)  # Convert QuerySet to a list
        random.shuffle(products)  # Shuffle the list of products

        # Paginate products
        paginator = Paginator(products, 30)  # Show 10 products per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)   # Adjust the category IDs as needed
        return render(request, 'accessories.html', {'products': page_obj, 'user': request.user})
class AccessoriesBeltsView(View):
    def get(self, request):
        # Fetch men's products
        products = Products.objects.filter(category_id='6')
        products = list(products)  # Convert QuerySet to a list
        random.shuffle(products)  # Shuffle the list of products

        # Paginate products
        paginator = Paginator(products, 30)  # Show 10 products per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)  # Adjust the category IDs as needed
        return render(request, 'accessories_belts.html', {'products': page_obj, 'user': request.user})

class AccessoriesSocksView(View):
    def get(self, request):
        # Fetch men's products
        products = Products.objects.filter(category_id='7')  # Adjust the category IDs as needed
        products = list(products)  # Convert QuerySet to a list
        random.shuffle(products)  # Shuffle the list of products

        # Paginate products
        paginator = Paginator(products, 30)  # Show 10 products per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Return rendered page with products
        return render(request, 'accessories_socks.html', {'products': page_obj, 'user': request.user})
       

class verify_email(View):
    def get(self, request):
        token = request.GET.get('token')
        user_email = email_verify.objects.filter(token=token).last()
        if user_email:
            user = User.objects.filter(email=user_email.email).last()

            user.email_verified = True
            user.save()
            return redirect ('/')
        else:
            return HttpResponse("User not found")





