from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control-custom',
            'placeholder': 'name@example.com',
            'autocomplete': 'email'
        })
    )
    first_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control-custom',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control-custom',
            'placeholder': 'Last Name'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Choose a username',
                'autocomplete': 'username'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control-custom',
            'placeholder': 'Create strong password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control-custom',
            'placeholder': 'Confirm password'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control-custom',
            'placeholder': 'Username or Email',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control-custom',
            'placeholder': 'Password',
            'autocomplete': 'current-password'
        })
    )


class UserProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control-custom', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control-custom', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control-custom', 'placeholder': 'Email'})
    )

    MOOD_CHOICES = [
        ('happy', 'Happy - Uplifting & Comedy'),
        ('sad', 'Sad - Emotional & Touching Drama'),
        ('relaxed', 'Relaxed - Chill & Peaceful'),
        ('stressed', 'Stressed - Pure Escapism & Fun'),
        ('adventurous', 'Adventurous - Thrills & Sci-Fi'),
        ('romantic', 'Romantic - Love & Warmth'),
    ]

    preferred_moods_select = forms.MultipleChoiceField(
        choices=MOOD_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'mood-checkbox-item'})
    )

    class Meta:
        model = UserProfile
        fields = ('bio', 'preferred_genres')
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control-custom',
                'rows': 3,
                'placeholder': 'Tell us about your cinematic taste...'
            }),
            'preferred_genres': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'e.g. Sci-Fi, Drama, Animation'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            if self.instance and self.instance.preferred_moods:
                self.fields['preferred_moods_select'].initial = self.instance.get_preferred_moods_list()

