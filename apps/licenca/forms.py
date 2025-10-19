from django import forms
from .models import Licenca, PlanoLicenca

class LicencaForm(forms.ModelForm):
    """Formulário para criar ou editar uma licença."""
    
    class Meta:
        model = Licenca
        fields = ['empresa', 'plano', 'data_vencimento']
        widgets = {
            'data_vencimento': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['empresa'].widget.attrs.update({'class': 'form-control'})
        self.fields['plano'].widget.attrs.update({'class': 'form-control'})
        self.fields['data_vencimento'].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        data_vencimento = cleaned_data.get('data_vencimento')
        
        if data_vencimento and data_vencimento < timezone.now().date():
            self.add_error('data_vencimento', 'A data de vencimento não pode ser anterior à data atual.')
        return cleaned_data


class RenovacaoForm(forms.Form):
    """Formulário para renovar uma licença."""
    meses = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Meses de Renovação'
    )

    def clean_meses(self):
        meses = self.cleaned_data.get('meses')
        if meses <= 0:
            raise forms.ValidationError('O número de meses deve ser maior que zero.')
        return meses