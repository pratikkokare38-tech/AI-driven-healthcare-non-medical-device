from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import PhoneVerification

User = get_user_model()


def landing_page(request):
    """Show landing page if not authenticated"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/landing.html')


def register_view(request):
    """Register a new user with phone verification"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        phone = request.POST.get('phone')
        
        # Validate inputs
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
            phone=phone,
            role='patient'
        )
        
        # Generate and send OTP
        phone_verification, _ = PhoneVerification.objects.get_or_create(user=user)
        phone_verification.phone = phone
        otp = phone_verification.generate_otp()
        
        # TODO: Send OTP via SMS provider (Twilio, AWS SNS, etc.)
        print(f"[Test OTP] {phone}: {otp}")
        
        # Store OTP in session for display (for testing - remove in production)
        request.session[f'otp_test_{user.id}'] = otp
        
        messages.success(request, f'Account created! Your test OTP is: {otp}')
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
            is_valid, message = phone_verification.verify_otp(otp)
            
            if is_valid:
                messages.success(request, 'Phone verified! You can now log in.')
                return redirect('login')
            else:
                messages.error(request, message)
        except PhoneVerification.DoesNotExist:
            messages.error(request, 'Verification error. Please try again.')
    
    return render(request, 'accounts/verify_phone.html', {'user': user})


def resend_otp_view(request, user_id):
    """Resend OTP"""
    try:
        user = User.objects.get(id=user_id)
        phone_verification = PhoneVerification.objects.get(user=user)
        otp = phone_verification.generate_otp()
        
        # TODO: Send OTP via SMS
        print(f"[Test OTP] {user.phone}: {otp}")
        
        # Store OTP in session for display (for testing - remove in production)
        request.session[f'otp_test_{user.id}'] = otp
        
        messages.success(request, f'New OTP sent! Test code: {otp}')
        return redirect('verify_phone', user_id=user.id)
    except (User.DoesNotExist, PhoneVerification.DoesNotExist):
        messages.error(request, 'Error. Please try again.')
        return redirect('register')


def login_view(request):
    """Log in user"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        raw_username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Allow login via email by looking up the username from the email
        actual_username = raw_username
        try:
            if '@' in raw_username:
                user_obj = User.objects.filter(email=raw_username).first()
                if user_obj:
                    actual_username = user_obj.username
        except Exception:
            pass
            
        user = authenticate(request, username=actual_username, password=password)
        
        if user:
            login(request, user)
            messages.success(request, 'Welcome!')
            return redirect(request.GET.get('next', 'dashboard'))
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')


def logout_view(request):
    """Log out user"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


def forgot_password_view(request):
    """Forgot password - look up user by email/username, use their stored phone"""
    if request.method == 'POST':
        email_or_username = request.POST.get('email_or_username')
        
        try:
            # Find user by email or username
            user = User.objects.filter(
                Q(email=email_or_username) | Q(username=email_or_username)
            ).first()
            
            if not user:
                messages.error(request, 'Email or username not found.')
                return render(request, 'accounts/forgot_password.html')
            
            # Generate OTP and send to their stored phone
            phone_verification, _ = PhoneVerification.objects.get_or_create(user=user)
            otp = phone_verification.generate_otp()
            
            # TODO: Send OTP via SMS to user.phone
            print(f"[Test OTP] {user.phone}: {otp}")
            
            messages.success(request, f'OTP sent to {user.phone}!')
            return redirect('reset_password', user_id=user.id)
        except Exception as e:
            messages.error(request, 'Error processing request. Please try again.')
    
    return render(request, 'accounts/forgot_password.html')


def reset_password_view(request, user_id):
    """Reset password after phone verification"""
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
            is_valid, message = phone_verification.verify_otp(otp)
            
            if not is_valid:
                messages.error(request, message)
                return render(request, 'accounts/reset_password.html', {'user': user})
            
            # Verify passwords
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'accounts/reset_password.html', {'user': user})
            
            if len(new_password) < 6:
                messages.error(request, 'Password must be at least 6 characters.')
                return render(request, 'accounts/reset_password.html', {'user': user})
            
            # Update password
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Password reset successful! Log in with your new password.')
            return redirect('login')
        
        except PhoneVerification.DoesNotExist:
            messages.error(request, 'Error. Please try again.')
            return redirect('forgot_password')
    
    return render(request, 'accounts/reset_password.html', {'user': user})


@login_required
def profile_view(request):
    """Edit user profile"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.address = request.POST.get('address', user.address)
        user.gender = request.POST.get('gender', user.gender)
        
        if request.FILES.get('profile_picture'):
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        messages.success(request, 'Profile updated!')
        return redirect('profile')
    
    return render(request, 'accounts/profile.html', {'user': request.user})

