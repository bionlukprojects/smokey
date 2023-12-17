from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(max_length=20, label = "Username")
    password = forms.CharField(max_length=20, label="Password",widget=forms.PasswordInput)

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=20, label="Name")
    mailadress = forms.CharField(max_length=100, label="Mail Adress")
    password = forms.CharField(max_length=20, label="Password",widget=forms.PasswordInput)
    confirm = forms.CharField(max_length=20, label="Password Verification", widget=forms.PasswordInput)

    def clean(self):
        username = self.cleaned_data.get("username")
        mailadress = self.cleaned_data.get("mailadress")
        password = self.cleaned_data.get("password")
        confirm = self.cleaned_data.get("confirm")

        if password and confirm and password != confirm:
            raise forms.ValidationError("Passwords do not match")
        
        values = {
            "username": username,
            "mailadress": mailadress,
            "password": password,
        }

        return values