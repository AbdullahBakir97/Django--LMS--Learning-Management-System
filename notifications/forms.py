from django import forms
from .models import NotificationType

class NotificationTypeForm(forms.ModelForm):
    predefined_types = forms.ChoiceField(
        choices=[(type_name, type_name) for type_name in NotificationType.PREDEFINED_TYPES],
        required=False,
        label='Predefined Types'
    )
    custom_type = forms.CharField(
        max_length=100,
        required=False,
        label='Custom Type'
    )

    class Meta:
        model = NotificationType
        fields = ['predefined_types', 'custom_type']

    def clean(self):
        cleaned_data = super().clean()
        predefined_type = cleaned_data.get('predefined_types')
        custom_type = cleaned_data.get('custom_type')

        if not predefined_type and not custom_type:
            raise forms.ValidationError('You must select a predefined type or enter a custom type.')

        if predefined_type and custom_type:
            raise forms.ValidationError('You can only select one type: either a predefined type or a custom type.')

        return cleaned_data

    def save(self, commit=True):
        predefined_type = self.cleaned_data.get('predefined_types')
        custom_type = self.cleaned_data.get('custom_type')

        if predefined_type:
            self.instance.type_name = predefined_type
        elif custom_type:
            self.instance.type_name = custom_type

        return super().save(commit=commit)