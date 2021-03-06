# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime

from django.shortcuts import render
from django import http
from django.contrib.auth.models import User
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.contrib.auth import authenticate, login as init_login
from django.conf import settings

from.models import WalletSeed, FailedLogin

def serv_wallet(request):
    return render(request, "wallet.html")

def accept_remote_registration(request):
    if not request.POST:
        return http.HttpResponseBadRequest("Post only")

    username = request.POST['username']
    u = User.objects.filter(username=username)
    if u.exists():
        return http.HttpResponseBadRequest("Username already exists")

    try:
        encrypted_mnemonic = request.POST['encrypted_mnemonic']
    except IndexError:
        return http.HttpResponseBadRequest("Encrypted Mnemonic missing.")

    encrypted_password = request.POST['encrypted_password']

    user = u[0]
    user.encrypted_mnemonic = encrypted_mnemonic
    user.encrypted_password = encrypted_password
    user.save()

    return http.HttpResponse("OK")

def register_new_wallet_user(request):
    encrypted_mnemonic = request.POST['encrypted_mnemonic']
    password = request.POST['password']
    username = request.POST['username']

    user = User.objects.create(
        username=username,
        email=request.POST.get('email', ''),
    )
    user.set_password(password)
    user.save()

    wal = WalletSeed.objects.create(
        user=user, encrypted_mnemonic=encrypted_mnemonic
    )

    user = authenticate(username=username, password=password)
    init_login(request, user)

    return http.JsonResponse({
        'wallet_settings': wal.get_settings(),
    })

def login(request):
    """
    Authenticate the user. On failed attempts, record the event, and limit
    5 failed attempts every 15 minutes.
    """
    username = request.POST['username']
    password = request.POST['password']

    fithteen_minutes_ago = datetime.datetime.now() - datetime.timedelta(minutes=15)
    tries = FailedLogin.objects.filter(username=username, time__gt=fithteen_minutes_ago)
    try_count = tries.count()

    if try_count < settings.LOGIN_TRIES:
        user = authenticate(username=username, password=password)

        if user and user.is_authenticated():
            init_login(request, user)
            wal = WalletSeed.objects.get(user=request.user)

            return http.JsonResponse({
                'encrypted_mnemonic': wal.encrypted_mnemonic,
                'wallet_settings': wal.get_settings(),
            })
        else:
            FailedLogin.objects.create(username=username)
            tries_left = settings.LOGIN_TRIES - try_count
            return http.JsonResponse({"tries_left": tries_left}, status=401)

    time_of_next_try = tries.latest().time + datetime.timedelta(minutes=15)
    minutes_to_wait = (time_of_next_try - timezone.now()).total_seconds() / 60.0
    return http.JsonResponse({
        "login_timeout": "Try again in %.1f minutes." % minutes_to_wait
    }, status=401)

@csrf_exempt
def update_settings(request):
    seed = WalletSeed.objects.get(user=request.user)

    if 'change_cheats' in request.POST:
        seed.change_balances = request.POST['change_cheats']

    if 'deposit_cheats' in request.POST:
        seed.change_balances = request.POST['deposit_cheats']

    seed.save()
    return http.HttpResponse("OK")
