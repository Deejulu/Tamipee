from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from store.models import Order
from .models import Payment
import uuid
import hmac
import hashlib
import json


def generate_reference():
    return f"TIF-{uuid.uuid4().hex[:12].upper()}"


@login_required
def initiate_payment(request):
    order = Order.objects.filter(user=request.user, status='pending').last()
    if not order:
        return redirect('store:orders')
    reference = generate_reference()
    payment, _ = Payment.objects.get_or_create(
        order=order,
        defaults={
            'user': request.user,
            'reference': reference,
            'amount': order.total_amount,
        }
    )
    return render(request, 'payments/initiate.html', {
        'order': order,
        'payment': payment,
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
    })


@login_required
def verify_payment(request):
    reference = request.GET.get('reference')
    if not reference:
        return redirect('store:orders')
    payment = get_object_or_404(Payment, reference=reference, user=request.user)
    return render(request, 'payments/verify.html', {'payment': payment})


@login_required
def payment_success(request):
    return render(request, 'payments/success.html')


@login_required
def payment_failed(request):
    return render(request, 'payments/failed.html')


@csrf_exempt
def payment_callback(request):
    """Paystack webhook callback — verifies signature and updates payment status."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=400)

    paystack_secret = settings.PAYSTACK_SECRET_KEY.encode('utf-8')
    signature = request.headers.get('X-Paystack-Signature', '')
    computed = hmac.new(paystack_secret, request.body, hashlib.sha512).hexdigest()

    if not hmac.compare_digest(computed, signature):
        return JsonResponse({'status': 'invalid signature'}, status=400)

    payload = json.loads(request.body)
    event = payload.get('event')
    data = payload.get('data', {})
    reference = data.get('reference')

    if event == 'charge.success' and reference:
        try:
            payment = Payment.objects.get(reference=reference)
            if payment.status == 'success':
                return JsonResponse({'status': 'ok'})
            payment.status = 'success'
            payment.paystack_response = data
            payment.save()
            payment.order.apply_inventory()
            payment.order.status = 'confirmed'
            payment.order.save(update_fields=['status', 'updated_at'])
        except Payment.DoesNotExist:
            pass
        except ValueError:
            return JsonResponse({'status': 'insufficient stock'}, status=409)

    return JsonResponse({'status': 'ok'})


