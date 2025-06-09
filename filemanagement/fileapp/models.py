from django.db import models
from django.contrib.auth.models import AbstractUser

class UserMaster(models.Model):
    user_id = models.CharField(max_length=20, primary_key=True)
    user_name = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    section_id = models.CharField(max_length=20)
    password = models.CharField(max_length=128)
    registration_status = models.BooleanField(default=False)
    ac_status = models.CharField(
        max_length=10, 
        choices=[('active', 'Active'), ('closed', 'Closed')],
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'usermaster'
        
    def __str__(self):
        return f"{self.user_name} ({self.user_id})"

class File(models.Model):
    file_id = models.AutoField(primary_key=True)
    file_no = models.CharField(max_length=30, unique=True)
    file_content = models.FileField(upload_to='uploads/%Y/%m/%d/')
    uploaded_by = models.ForeignKey(
        UserMaster, 
        on_delete=models.CASCADE,
        related_name='uploaded_files'
    )
    current_owner = models.ForeignKey(  # Add this field
        UserMaster,
        on_delete=models.CASCADE,
        related_name='owned_files',
        null=True, blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_status = models.CharField(
        max_length=10, 
        choices=[('open', 'Open'), ('closed', 'Closed')],
        default='open'
    )
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"File {self.file_no}"


class FileLog(models.Model):
    log_id = models.AutoField(primary_key=True)
    log_date = models.DateTimeField(auto_now_add=True)
    file_no = models.ForeignKey(
        File, 
        on_delete=models.CASCADE,
        related_name='logs'
    )
    from_user = models.ForeignKey(
        UserMaster, 
        on_delete=models.CASCADE, 
        related_name='sent_logs'
    )
    to_user = models.ForeignKey(
        UserMaster, 
        on_delete=models.CASCADE, 
        related_name='received_logs'
    )
    status = models.CharField(
        max_length=15, 
        choices=[
            ('in_transit', 'In Transit'), 
            ('reverted', 'Reverted'), 
            ('completed', 'Completed')
        ],
        default='in_transit'
    )
    remarks = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'filelog'
        
    def __str__(self):
        return f"Log {self.log_id}: {self.file_no.file_no}"
