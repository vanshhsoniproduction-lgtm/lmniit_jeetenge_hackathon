import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings
from .models import PaymentRequest, PaymentTransaction
from web3 import Web3
from decimal import Decimal

# CONSTANTS
RECEIVER_WALLET = '0x9497FE4B4ECA41229b9337abAEbCC91eCc7be23B'
# Monad Testnet
RPC_URL = 'https://testnet-rpc.monad.xyz'
CHAIN_ID = 10143

def get_web3():
    return Web3(Web3.HTTPProvider(RPC_URL))

# 1. PROFILE / HOME
@login_required
def profile_view(request):
    return render(request, 'payment/profile.html', {
        'receiver_wallet': RECEIVER_WALLET
    })

# 2. STATIC QR
@login_required
def static_qr_view(request):
    """Show the Static QR code for fixed payments."""
    return render(request, 'payment/static_qr.html', {
        'receiver_wallet': RECEIVER_WALLET,
        'amount': None # User chooses
    })

@login_required
def pay_static_view(request):
    """Payment page for Static QR"""
    return render(request, 'payment/pay.html', {
        'mode': 'STATIC',
        'receiver_wallet': RECEIVER_WALLET,
        'amount': None, # User input needed
        'note': 'Direct Transfer to Wallet',
        'request_id': None
    })

# 3. DYNAMIC QR
@login_required
def create_dynamic_qr(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        note = request.POST.get('note')
        
        pr = PaymentRequest.objects.create(
            request_type='DYNAMIC',
            amount_mon=amount,
            note=note,
            receiver_wallet=RECEIVER_WALLET
        )
        return render(request, 'payment/dynamic_qr_show.html', {'payment_request': pr})
        
    return render(request, 'payment/create_qr.html')

@login_required
def pay_dynamic_view(request, request_id):
    pr = get_object_or_404(PaymentRequest, id=request_id)
    
    if pr.status == 'PAID':
        # If already paid, find the tx and redirect to receipt
        last_tx = pr.transactions.filter(verified=True).last()
        if last_tx:
            return redirect('receipt', tx_hash=last_tx.tx_hash)

    return render(request, 'payment/pay.html', {
        'mode': 'DYNAMIC',
        'receiver_wallet': pr.receiver_wallet,
        'amount': pr.amount_mon,
        'note': pr.note,
        'request_id': str(pr.id)
    })


# 4. VERIFICATION API
@login_required
def verify_transaction(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    data = json.loads(request.body)
    tx_hash = data.get('tx_hash')
    request_id = data.get('request_id') # Optional for static
    
    if not tx_hash:
        return JsonResponse({'error': 'Missing tx_hash'}, status=400)

    # 1. Check if we already have this tx
    if PaymentTransaction.objects.filter(tx_hash=tx_hash).exists():
         return JsonResponse({'success': True, 'message': 'Already processed'})

    # 2. Verify on Chain
    w3 = get_web3()
    try:
        # Applying Patch for IPv4 (Windows Fix) if needed
        import socket
        original_getaddrinfo = socket.getaddrinfo
        def new_getaddrinfo(*args, **kwargs):
            responses = original_getaddrinfo(*args, **kwargs)
            return [res for res in responses if res[0] == socket.AF_INET]
        socket.getaddrinfo = new_getaddrinfo
        
        try:
            tx = w3.eth.get_transaction(tx_hash)
            receipt = w3.eth.get_transaction_receipt(tx_hash)
        finally:
            socket.getaddrinfo = original_getaddrinfo
        
        if not tx or not receipt:
             return JsonResponse({'error': 'Transaction not found on chain'}, status=404)
        if receipt['status'] != 1:
             return JsonResponse({'error': 'Transaction failed on chain'}, status=400)
             
        # Check Receiver
        if tx['to'].lower() != RECEIVER_WALLET.lower():
             return JsonResponse({'error': 'Invalid receiver address'}, status=400)
             
        val_eth = w3.from_wei(tx['value'], 'ether')
        
        payment_req = None
        
        # Scenario A: Dynamic Request
        if request_id and request_id != 'None':
            try:
                payment_req = PaymentRequest.objects.get(id=request_id)
                # Mark Paid
                payment_req.status = 'PAID'
                payment_req.paid_at = timezone.now()
                payment_req.save()
            except PaymentRequest.DoesNotExist:
                pass 
                
        # Scenario B: Static Request (Create new Record)
        if not payment_req:
             payment_req = PaymentRequest.objects.create(
                 request_type='STATIC',
                 amount_mon=val_eth,
                 receiver_wallet=RECEIVER_WALLET,
                 status='PAID',
                 paid_at=timezone.now(),
                 note='Static PayLink Transfer'
             )

        # Save Transaction
        PaymentTransaction.objects.create(
            request=payment_req,
            payer_wallet=tx['from'],
            tx_hash=tx_hash,
            amount_mon=val_eth,
            verified=True,
            chain_id=str(CHAIN_ID)
        )
        
        return JsonResponse({'success': True})

    except Exception as e:
        print(f"Verify Error: {e}")
        return JsonResponse({'error': str(e)}, status=500)


# 5. RECEIPT & HISTORY
@login_required
def receipt_view(request, tx_hash):
    tx = get_object_or_404(PaymentTransaction, tx_hash=tx_hash)
    return render(request, 'payment/receipt.html', {'transaction': tx})

@login_required
def payment_history(request):
    # Show all paid requests or transactions?
    # Let's show transactions which are proofs of payment
    txs = PaymentTransaction.objects.all().order_by('-created_at')
    return render(request, 'payment/history.html', {'transactions': txs})
