from django import forms
from .models import UserMaster, File, FileLog

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = UserMaster
        fields = ['user_id', 'user_name', 'designation', 'section_id', 'password']
        
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords don't match")
        
        return cleaned_data

class FileUploadForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ['file_no', 'file_content', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'file_content': forms.FileInput(attrs={'accept': '.pdf,.doc,.docx,.txt'})
        }

class FileTransferForm(forms.ModelForm):
    class Meta:
        model = FileLog
        fields = ['to_user', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 2}),
        }
