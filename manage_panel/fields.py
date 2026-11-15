from django import forms


class MultipleFileInput(forms.ClearableFileInput):
    """
    Custom ClearableFileInput widget for Django 5+/6 that explicitly allows
    selecting and uploading multiple files in a single input.
    """
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """
    Form field returning a list of UploadedFile objects when multiple files
    are selected via MultipleFileInput.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={"multiple": True, "class": "form-control", "accept": "image/jpeg,image/png,image/webp,image/gif"}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            if not data and self.required:
                raise forms.ValidationError(self.error_messages["required"], code="required")
            return [single_file_clean(d, initial) for d in data if d]
        if data:
            return [single_file_clean(data, initial)]
        if self.required:
            raise forms.ValidationError(self.error_messages["required"], code="required")
        return []

