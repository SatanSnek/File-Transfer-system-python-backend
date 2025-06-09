from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import UserMaster, File, FileLog
from .forms import UserRegistrationForm, FileUploadForm, FileTransferForm
from django.http import HttpResponse, FileResponse, Http404

def dashboard(request):
    """Main dashboard view"""
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = get_object_or_404(UserMaster, user_id=request.session['user_id'])
    
    # Get user's files
    user_files = File.objects.filter(uploaded_by=user).order_by('-uploaded_at')[:5]
    
    # Get recent logs
    recent_logs = FileLog.objects.filter(
        Q(from_user=user) | Q(to_user=user)
    ).order_by('-log_date')[:10]
    
    context = {
        'user': user,
        'user_files': user_files,
        'recent_logs': recent_logs,
        'total_files': File.objects.filter(uploaded_by=user).count(),
        'pending_files': FileLog.objects.filter(to_user=user, status='in_transit').count(),
    }
    
    return render(request, 'fileapp/dashboard.html', context)

def register_user(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Hash password (in production, use proper password hashing)
            user.password = form.cleaned_data['password']
            user.save()
            messages.success(request, 'User registered successfully!')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'fileapp/register.html', {'form': form})

def user_login(request):
    """User login view"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        password = request.POST.get('password')
        
        try:
            user = UserMaster.objects.get(user_id=user_id, password=password, ac_status='active')
            request.session['user_id'] = user.user_id
            request.session['user_name'] = user.user_name
            messages.success(request, f'Welcome back, {user.user_name}!')
            return redirect('dashboard')
        except UserMaster.DoesNotExist:
            messages.error(request, 'Invalid credentials or inactive account')
    
    return render(request, 'fileapp/login.html')

def upload_file(request):
    """File upload view"""
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = get_object_or_404(UserMaster, user_id=request.session['user_id'])
    
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_obj = form.save(commit=False)
            file_obj.uploaded_by = user
            file_obj.save()
            messages.success(request, 'File uploaded successfully!')
            return redirect('file_list')
    else:
        form = FileUploadForm()
    
    return render(request, 'fileapp/upload_file.html', {'form': form})

def file_list(request):
    """List all files accessible to the user"""
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = get_object_or_404(UserMaster, user_id=request.session['user_id'])
    
    # Use Q objects instead of UNION to avoid Oracle NCLOB issues
    from django.db.models import Q
    
    # Get files uploaded by user OR files transferred to user and completed
    accepted_file_ids = FileLog.objects.filter(
        to_user=user, 
        status='completed'
    ).values_list('file_no_id', flat=True)
    
    # Single query using Q objects instead of UNION
    all_files = File.objects.filter(
        Q(uploaded_by=user) | Q(file_id__in=accepted_file_ids)
    ).distinct().order_by('-uploaded_at')
    
    # Pagination
    paginator = Paginator(all_files, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'fileapp/file_list.html', {'page_obj': page_obj})

def transfer_file(request, file_id):
    """Transfer file to another user"""
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = get_object_or_404(UserMaster, user_id=request.session['user_id'])
    file_obj = get_object_or_404(File, file_id=file_id, uploaded_by=user)
    
    if request.method == 'POST':
        form = FileTransferForm(request.POST)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.file_no = file_obj
            transfer.from_user = user
            transfer.save()
            messages.success(request, 'File transferred successfully!')
            return redirect('file_list')
    else:
        form = FileTransferForm()
    
    # Get available users for transfer
    available_users = UserMaster.objects.filter(ac_status='active').exclude(user_id=user.user_id)
    
    return render(request, 'fileapp/transfer_file.html', {
        'form': form,
        'file_obj': file_obj,
        'available_users': available_users
    })

def file_logs(request):
    """View file transfer logs"""
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = get_object_or_404(UserMaster, user_id=request.session['user_id'])
    logs = FileLog.objects.filter(
        Q(from_user=user) | Q(to_user=user)
    ).order_by('-log_date')
    
    # Pagination
    paginator = Paginator(logs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'fileapp/file_logs.html', {'page_obj': page_obj})

def logout_user(request):
    """User logout"""
    request.session.flush()
    messages.success(request, 'Logged out successfully!')
    return redirect('login')
def pending_files(request):
    """View pending file transfers for the current user"""
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = get_object_or_404(UserMaster, user_id=request.session['user_id'])
    
    # Get files transferred to this user that are still in transit
    pending_transfers = FileLog.objects.filter(
        to_user=user, 
        status='in_transit'
    ).order_by('-log_date')
    
    return render(request, 'fileapp/pending_files.html', {
        'pending_transfers': pending_transfers
    })

def accept_file(request, log_id):
    """Accept a transferred file"""
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = get_object_or_404(UserMaster, user_id=request.session['user_id'])
    log_entry = get_object_or_404(FileLog, log_id=log_id, to_user=user, status='in_transit')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'accept':
            # Update log status to completed
            log_entry.status = 'completed'
            log_entry.save()
            
            # Transfer ownership completely - file no longer belongs to sender
            file_obj = log_entry.file_no
            file_obj.uploaded_by = user  # Change ownership to receiver
            file_obj.current_owner = user
            file_obj.save()
            
            messages.success(request, f'File {file_obj.file_no} accepted and transferred to you!')
            
        elif action == 'reject':
            log_entry.status = 'reverted'
            log_entry.save()
            messages.info(request, f'File {log_entry.file_no.file_no} rejected and reverted to sender.')
        
        return redirect('pending_files')
    
    return render(request, 'fileapp/accept_file.html', {'log_entry': log_entry})

def download_file(request, file_id):
    """Download file if user has access"""
    if 'user_id' not in request.session:
        return redirect('login')
    
    user = get_object_or_404(UserMaster, user_id=request.session['user_id'])
    file_obj = get_object_or_404(File, file_id=file_id)
    
    # Check if user has access to the file
    has_access = (
        file_obj.uploaded_by == user or  # Original uploader
        file_obj.current_owner == user or  # Current owner
        FileLog.objects.filter(  # Has received the file
            file_no=file_obj, 
            to_user=user, 
            status='completed'
        ).exists()
    )
    
    if not has_access:
        messages.error(request, 'You do not have permission to access this file.')
        return redirect('dashboard')
    
    # Serve the file
    response = HttpResponse(file_obj.file_content.read(), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{file_obj.file_content.name}"'
    return response