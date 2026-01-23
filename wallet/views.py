import json
import uuid
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from eth_account import Account
from eth_account.messages import encode_defunct
from .models import WalletUser

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')

def get_nonce(request):
    """
    Get or create a user based on wallet address and return their nonce.
    """
    address = request.GET.get('address')
    if not address:
        return JsonResponse({'error': 'Address required'}, status=400)
    
    # Normalize address
    address = address.lower()
    
    # Get or create user
    user, created = WalletUser.objects.get_or_create(wallet_address=address)
    
    return JsonResponse({'nonce': str(user.nonce)})

@require_POST
def verify_signature(request):
    """
    Verify the signature sent by frontend.
    1. Reconstruct the message using the user's nonce.
    2. Recover the signer address.
    3. Match with DB.
    4. Login user.
    """
    data = json.loads(request.body)
    address = data.get('address', '').lower()
    signature = data.get('signature')

    if not address or not signature:
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        user = WalletUser.objects.get(wallet_address=address)
    except WalletUser.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    # 1. Reconstruct the message that was signed on frontend
    # MUST match the string format in the JavaScript exactly!
    message_text = f"Sign this message to log in to Django DApp: {user.nonce}"
    
    # 2. Encode for eth-account verification
    encoded_msg = encode_defunct(text=message_text)
    
    # 3. Recover address from signature
    recovered_address = Account.recover_message(encoded_msg, signature=signature)

    # 4. Verify match
    if recovered_address.lower() == address:
        # Login successful
        login(request, user)
        
        # Rotate nonce to prevent replay attacks
        user.nonce = uuid.uuid4()
        user.save()
        
        return JsonResponse({'success': True, 'redirect_url': '/dashboard/'})
    else:
        return JsonResponse({'error': 'Invalid signature'}, status=400)

@login_required
def dashboard(request):
    return render(request, 'dashboard.html', {'user': request.user})

def logout_view(request):
    logout(request)
    return redirect('/')