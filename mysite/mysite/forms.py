from django.contrib.auth.forms import AuthenticationForm

class LoginFrm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for filed in self.fileds.values():
            field.widget.attr['class']='form-control'
            field.widget.attr['placeholder']=field.label