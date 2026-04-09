from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import PhoneVerification

User = get_user_model()


def landing_page(request):
    """Show landing page if not authenticated"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/landing.html')


def register_view(request):
    """Register a new user"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        phone = request.POST.get('phone', '')
        
        # Validation
        if password != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/register.html')
        
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(phone=phone).exists():
            messages.error(request, 'Phone number already registered.')
            return render(request, 'accounts/register.html')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role='patient'
        )
        
        # Generate phone verification OTP
        phone_verification, created = PhoneVerification.objects.get_or_create(user=user)
        phone_verification.phone = phone
        otp = phone_verification.generate_otp()
        
        # TODO: Send OTP via SMS (integrate SMS service here)
        print(f"OTP for {phone}: {otp}")  # For testing
        
        messages.success(request, 'User created! Verify your phone number.')
        return redirect('verify_phone', user_id=user.id)
    
    return render(request, 'accounts/register.html')


def verify_phone_view(request, user_id):
    """Verify phone number with OTP"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('register')
    
    if request.method == 'POST':
        otp = request.POST.get('otp')
        
        try:
            phone_verification = PhoneVerification.objects.get(user=user)
            success, message = phone_verification.verify_otp(otp)
            
            if success:
                messages.success(request, 'Phone verified successfully! You can now log in.')
                return redirect('login')
            else:
                messages.error(request, message)
        except PhoneVerification.DoesNotExist:
            messages.error(request, 'Verification error. Please register again.')
            return redirect('register')
    
    return render(request, 'accounts/verify_phone.html', {'user': user})


def resend_otp_view(request, user_id):
    """Resend OTP to phone"""
    try:
        user = User.objects.get(id=user_id)
        phone_verification = PhoneVerification.objects.get(user=user)
        otp = phone_verification.generate_otp()
        
        # TODO: Send OTP via SMS
        print(f"OTP for {user.phone}: {otp}")
        
        messages.success(request, 'OTP sent to your phone!')
        return redirect('verify_phone', user_id=user.id)
    except (User.DoesNotExist, PhoneVerification.DoesNotExist):
        messages.error(request, 'Error sending OTP.')
        return redirect('register')


def login_view(request):
    """Log in a user"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user:
            # Check if phone is verified
            if not user.phone_verified:
                messages.warning(request, 'Please verify your phone number first.')
                try:
                    phone_verification = PhoneVerification.objects.get(user=user)
                    otp = phone_verification.generate_otp()
                    print(f"OTP for {user.phone}: {otp}")
                except:
                    pass
                return redirect('verify_phone', user_id=user.id)
            
            login(request, user)
            messages.success(request, f'Welcome back!')
            return redirect(request.GET.get('next', 'dashboard'))
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')


def logout_view(request):
    """Log out a user"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


def forgot_password_view(request):
    """Start forgot password process with phone verification"""
    if request.method == 'POST':
        phone = request.POST.get('phone')
        
        try:
            user = User.objects.get(phone=phone)
            phone_verification = PhoneVerification.objects.get(user=user)
            otp = phone_verification.generate_otp()
            
            # TODO: Send OTP via SMS
            print(f"Password reset OTP for {phone}: {otp}")
            
            messages.success(request, 'OTP sent to your phone!')
            return redirect('verify_phone_reset', user_id=user.id)
        except (User.DoesNotExist, PhoneVerification.DoesNotExist):
            messages.error(request, 'Phone number not found.')
    
    return render(request, 'accounts/forgot_password.html')


def verify_phone_reset_view(request, user_id):
    """Verify phone for password reset"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        otp = request.POST.get('otp')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Verify OTP
        try:
            phone_verification = PhoneVerification.objects.get(user=user)
            success, message = phone_verification.verify_otp(otp)
            
            if not success:
                messages.error(request, message)
                return render(request, 'accounts/verify_phone_reset.html', {'user': user})
            
            # Check passwords match
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'accounts/verify_phone_reset.html', {'user': user})
            
            if len(new_password) < 6:
                messages.error(request, 'Password must be at least 6 characters.')
                return render(request, 'accounts/verify_phone_reset.html', {'user': user})
            
            # Update password
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Password reset successful! You can now log in.')
            return redirect('login')
        
        except PhoneVerification.DoesNotExist:
            messages.error(request, 'Verification error.')
            return redirect('forgot_password')
    
    return render(request, 'accounts/verify_phone_reset.html', {'user': user})


@login_required
def profile_view(request):
    """Edit user profile"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        user.address = request.POST.get('address', user.address)
        user.gender = request.POST.get('gender', user.gender)
        
        if request.FILES.get('profile_picture'):
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    return render(request, 'accounts/profile.html', {'user': request.user})
