from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.contrib import messages
import os
from .models import UserMaster, File, FileLog

def delete_files_and_records(modeladmin, request, queryset):
    """Custom admin action to delete files and database records"""
    deleted_files = 0
    deleted_records = 0
    
    for obj in queryset:
        # Delete physical file first
        if obj.file_content:
            try:
                if default_storage.exists(obj.file_content.name):
                    default_storage.delete(obj.file_content.name)
                    deleted_files += 1
                    print(f"Deleted file: {obj.file_content.name}")  # Debug
            except Exception as e:
                print(f"Error deleting file {obj.file_content.name}: {e}")  # Debug
        
        # Delete database record
        try:
            obj.delete()
            deleted_records += 1
        except Exception as e:
            print(f"Error deleting record {obj.file_no}: {e}")  # Debug
    
    messages.success(
        request, 
        f'Successfully deleted {deleted_files} files and {deleted_records} records.'
    )

delete_files_and_records.short_description = "Delete selected files and records"

@admin.register(UserMaster)
class UserMasterAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'user_name', 'designation', 'section_id', 'ac_status', 'registration_status']
    list_filter = ['ac_status', 'registration_status', 'designation']
    search_fields = ['user_id', 'user_name', 'section_id']

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ['file_no', 'uploaded_by', 'file_link', 'file_size', 'uploaded_at', 'file_status']
    list_filter = ['file_status', 'uploaded_at']
    search_fields = ['file_no', 'uploaded_by__user_name']
    readonly_fields = ['file_preview', 'file_info']
    actions = [delete_files_and_records]
    
    def file_link(self, obj):
        """Create a clickable link to download the file"""
        if obj.file_content:
            url = obj.file_content.url
            return format_html('<a href="{}" target="_blank">Download</a>', url)
        return "No file"
    file_link.short_description = "File"
    
    def file_size(self, obj):
        """Display file size"""
        if obj.file_content:
            try:
                size_bytes = obj.file_content.size
                if size_bytes < 1024:
                    return f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    return f"{size_bytes / 1024:.1f} KB"
                else:
                    return f"{size_bytes / (1024 * 1024):.1f} MB"
            except:
                return "Unknown"
        return "No file"
    file_size.short_description = "Size"
    
    def file_preview(self, obj):
        """Show file information in admin detail view"""
        if obj.file_content:
            return format_html(
                '<p><strong>File:</strong> {}<br>'
                '<strong>Size:</strong> {}<br>'
                '<strong>Path:</strong> {}</p>',
                obj.file_content.name,
                self.file_size(obj),
                obj.file_content.path if hasattr(obj.file_content, 'path') else 'Remote storage'
            )
        return "No file attached"
    file_preview.short_description = "File Information"
    
    def file_info(self, obj):
        """Additional file information"""
        if obj.file_content:
            exists = default_storage.exists(obj.file_content.name)
            status = "✅ Exists" if exists else "❌ Missing"
            return format_html('<span>{}</span>', status)
        return "No file"
    file_info.short_description = "File Status"
    
    def delete_model(self, request, obj):
        """Override delete_model to delete physical file when deleting single record"""
        if obj.file_content:
            try:
                if default_storage.exists(obj.file_content.name):
                    default_storage.delete(obj.file_content.name)
                    messages.success(request, f'File {obj.file_content.name} deleted from storage.')
            except Exception as e:
                messages.error(request, f'Error deleting file: {e}')
        
        super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        """Override delete_queryset to delete physical files when bulk deleting"""
        deleted_files = 0
        for obj in queryset:
            if obj.file_content:
                try:
                    if default_storage.exists(obj.file_content.name):
                        default_storage.delete(obj.file_content.name)
                        deleted_files += 1
                except Exception as e:
                    messages.error(request, f'Error deleting file {obj.file_content.name}: {e}')
        
        super().delete_queryset(request, queryset)
        messages.success(request, f'Deleted {deleted_files} files from storage.')

@admin.register(FileLog)
class FileLogAdmin(admin.ModelAdmin):
    list_display = ['log_id', 'file_no', 'from_user', 'to_user', 'status', 'log_date']
    list_filter = ['status', 'log_date']
    search_fields = ['file_no__file_no', 'from_user__user_name', 'to_user__user_name']
    readonly_fields = ['log_date']
    
    def has_add_permission(self, request):
        """Prevent manual creation of file logs through admin"""
        return False
