from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import AddressForm, ProfileForm, SignupForm
from .models import Address


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to Spice Garden! Your account is ready.")
            return redirect("home")
    else:
        form = SignupForm()
    return render(request, "signup.html", {"form": form})


@login_required
def profile(request):
    profile_form = ProfileForm(instance=request.user)
    address_form = AddressForm(initial={"full_name": request.user.get_full_name()})

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "profile":
            profile_form = ProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated.")
                return redirect("profile")
        elif action == "address":
            address_form = AddressForm(request.POST)
            if address_form.is_valid():
                address = address_form.save(commit=False)
                address.user = request.user
                address.save()
                messages.success(request, "Address saved.")
                return redirect("profile")

    return render(request, "profile.html", {
        "profile_form": profile_form,
        "address_form": address_form,
        "addresses": request.user.addresses.all(),
    })


@login_required
@require_POST
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    messages.success(request, "Address removed.")
    return redirect("profile")
