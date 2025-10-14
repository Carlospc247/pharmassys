# apps/funcionarios/forms.py
from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import Funcionario, Cargo, Departamento, EscalaTrabalho, Ferias, Capacitacao, AvaliacaoDesempenho, JornadaTrabalho, RegistroPonto, Comunicado
from datetime import date, timedelta

User = get_user_model()




class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = '__all__'
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
            'data_admissao': forms.DateInput(attrs={'type': 'date'}),
            'data_demissao': forms.DateInput(attrs={'type': 'date'}),
            'data_fim_experiencia': forms.DateInput(attrs={'type': 'date'}),
            'foto': forms.FileInput(),
        }

    def clean_bi(self):
        bi = self.cleaned_data['bi']
        if Funcionario.objects.exclude(pk=self.instance.pk).filter(bi=bi).exists():
            raise ValidationError("BI já cadastrado para outro funcionário.")
        return bi

    def clean_data_demissao(self):
        data_demissao = self.cleaned_data.get('data_demissao')
        data_admissao = self.cleaned_data.get('data_admissao')
        if data_demissao and data_admissao and data_demissao <= data_admissao:
            raise ValidationError("Data de demissão deve ser posterior à data de admissão.")
        return data_demissao


    def clean(self):
        cleaned_data = super().clean()
        data_admissao = cleaned_data.get('data_admissao')
        periodo_experiencia = cleaned_data.get('periodo_experiencia_dias')

        if data_admissao and periodo_experiencia:
            cleaned_data['data_fim_experiencia'] = data_admissao + timedelta(days=periodo_experiencia)

        return cleaned_data


class EscalaTrabalhoForm(forms.ModelForm):
    class Meta:
        model = EscalaTrabalho
        fields = [
            'funcionario', 'data_trabalho', 'turno', 'horario_entrada', 'horario_saida',
            'horario_almoco_inicio', 'horario_almoco_fim', 'loja', 'departamento',
            'funcao_dia', 'confirmada', 'trabalhada', 'observacoes', 'criada_por'
        ]
        widgets = {
            'data_trabalho': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        entrada = cleaned_data.get('horario_entrada')
        saida = cleaned_data.get('horario_saida')
        if entrada and saida and entrada >= saida:
            raise ValidationError("Horário de saída deve ser maior que horário de entrada.")
        return cleaned_data


class FeriasForm(forms.ModelForm):
    class Meta:
        model = Ferias
        fields = [
            'funcionario', 'periodo_aquisitivo_inicio', 'periodo_aquisitivo_fim',
            'data_inicio', 'data_fim', 'dias_ferias', 'adiantamento_13', 'status',
            'aprovada_por', 'data_aprovacao', 'observacoes'
        ]
        widgets = {
            'periodo_aquisitivo_inicio': forms.DateInput(attrs={'type': 'date'}),
            'periodo_aquisitivo_fim': forms.DateInput(attrs={'type': 'date'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'}),
            'data_aprovacao': forms.DateInput(attrs={'type': 'date'}),
        }


class CapacitacaoForm(forms.ModelForm):
    class Meta:
        model = Capacitacao
        fields = [
            'funcionario', 'titulo', 'descricao', 'tipo', 'carga_horaria',
            'data_inicio', 'data_fim', 'instituicao', 'instrutor', 'local', 'modalidade',
            'valor_inscricao', 'valor_transporte', 'valor_hospedagem', 'valor_alimentacao',
            'status', 'nota_final', 'certificado', 'aprovada_por', 'observacoes'
        ]
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'}),
            'certificado': forms.FileInput(),
        }


class AvaliacaoDesempenhoForm(forms.ModelForm):
    class Meta:
        model = AvaliacaoDesempenho
        fields = [
            'funcionario', 'tipo_avaliacao', 'periodo_inicio', 'periodo_fim', 'data_avaliacao',
            'avaliador', 'pontualidade', 'assiduidade', 'qualidade_trabalho', 'produtividade',
            'iniciativa', 'relacionamento_interpessoal', 'conhecimento_tecnico', 'lideranca',
            'pontos_fortes', 'pontos_melhorar', 'metas_objetivos', 'plano_desenvolvimento',
            'recomenda_promocao', 'recomenda_aumento', 'recomenda_capacitacao', 'observacoes'
        ]
        widgets = {
            'periodo_inicio': forms.DateInput(attrs={'type': 'date'}),
            'periodo_fim': forms.DateInput(attrs={'type': 'date'}),
            'data_avaliacao': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Nota geral calculada automaticamente
        notas = [
            cleaned_data.get('pontualidade'),
            cleaned_data.get('assiduidade'),
            cleaned_data.get('qualidade_trabalho'),
            cleaned_data.get('produtividade'),
            cleaned_data.get('iniciativa'),
            cleaned_data.get('relacionamento_interpessoal'),
            cleaned_data.get('conhecimento_tecnico')
        ]
        lideranca = cleaned_data.get('lideranca')
        if lideranca:
            notas.append(lideranca)

        if None not in notas:
            cleaned_data['nota_geral'] = sum(notas) / len(notas)

        return cleaned_data


class CargoForm(forms.ModelForm):
    class Meta:
        model = Cargo
        fields = [
            'nome', 'codigo', 'descricao', 'cargo_superior', 'nivel_hierarquico',
            'categoria', 'salario_base', 'vale_alimentacao', 'vale_transporte',
            'pode_pagar_salario', 'pode_vender', 'pode_fazer_desconto',
            'limite_desconto_percentual', 'pode_cancelar_venda', 'pode_fazer_devolucao',
            'pode_alterar_preco', 'pode_gerenciar_estoque', 'pode_fazer_compras',
            'pode_aprovar_pedidos', 'pode_gerenciar_funcionarios', 'pode_editar_produtos',
            'pode_emitir_faturacredito', 'pode_liquidar_faturacredito', 'pode_emitir_proforma',
            'pode_aprovar_proforma', 'ativo',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do cargo'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código único'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição do cargo'}),
            'cargo_superior': forms.Select(attrs={'class': 'form-control'}),
            'nivel_hierarquico': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'salario_base': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'vale_alimentacao': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'vale_transporte': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'limite_desconto_percentual': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            # ⚡ widgets para os booleans
            'pode_pagar_salario': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'pode_vender': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'pode_fazer_desconto': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'pode_cancelar_venda': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'pode_fazer_devolucao': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'pode_alterar_preco': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'pode_gerenciar_estoque': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'pode_fazer_compras': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'pode_aprovar_pedidos': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'pode_gerenciar_funcionarios': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'pode_editar_produtos': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'pode_emitir_faturacredito': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'pode_liquidar_faturacredito': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'pode_emitir_proforma': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'pode_aprovar_proforma': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


    def clean(self):
        """
        Garante a coerência entre as permissões booleanas e seus limites/contextos.
        """
        cleaned_data = super().clean()

        # --- Regra 1: Coerência de Desconto ---
        pode_fazer_desconto = cleaned_data.get('pode_fazer_desconto')
        limite_desconto = cleaned_data.get('limite_desconto_percentual', Decimal('0'))

        if limite_desconto is None:
            limite_desconto = Decimal('0')
        
        # Se não pode fazer desconto, o limite deve ser zero.
        if not pode_fazer_desconto and limite_desconto > Decimal('0'):
            # Força o valor a zero e adiciona um aviso (não impede o save)
            self.add_error('limite_desconto_percentual', 
                           "O limite de desconto deve ser 0% se o cargo não tiver permissão para descontar.")
            cleaned_data['limite_desconto_percentual'] = Decimal('0') # Correção automática
        
        # Se pode fazer desconto, mas o limite é zero ou nulo, forçamos um erro.
        elif pode_fazer_desconto and limite_desconto <= Decimal('0'):
             raise ValidationError(
                {'limite_desconto_percentual': "Se o cargo pode fazer desconto, o limite percentual deve ser maior que 0."},
                code='limite_invalido'
            )
        
        # --- Regra 2: Aprovação de Documentos Fiscais (Hierarquia de Poder) ---
        pode_aprovar_proforma = cleaned_data.get('pode_aprovar_proforma')
        pode_emitir_proforma = cleaned_data.get('pode_emitir_proforma')
        
        # É uma regra de negócio forte: quem aprova deve ter uma hierarquia de poder.
        # Se puder aprovar, deve ter pelo menos a permissão de emitir ou o sistema fica incoerente.
        if pode_aprovar_proforma and not pode_emitir_proforma:
            raise ValidationError(
                {'pode_aprovar_proforma': "O cargo não pode ter permissão apenas para Aprovar Proforma sem poder Emiti-la. Ajuste as permissões."},
                code='inconsistencia_aprovacao'
            )

        # --- Regra 3: Permissões Críticas e Nível Hierárquico (Exemplo) ---
        pode_pagar_salario = cleaned_data.get('pode_pagar_salario')
        nivel_hierarquico = cleaned_data.get('nivel_hierarquico')
        categoria = cleaned_data.get('categoria')
        
        # Exemplo de regra empresarial: Apenas cargos de alta gerência/RH podem pagar salário.
        # Assumindo que Nível 5 é "baixo" (operacional) e Nível 1 é "alto" (diretoria).
        if pode_pagar_salario and nivel_hierarquico > 3 and categoria not in ['rh', 'diretoria', 'gerencia']:
            raise ValidationError(
                {'pode_pagar_salario': "Somente cargos de RH, Diretoria ou Nível Hierárquico até 3 podem pagar salário."},
                code='nivel_inadequado'
            )

        return cleaned_data





class DepartamentoForm(forms.ModelForm):
    class Meta:
        model = Departamento
        fields = [
            'nome',
            'codigo',
            'descricao',
            'responsavel',
            'loja',
            'centro_custo',
            'ativo',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do departamento'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código único'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição do departamento'}),
            'responsavel': forms.Select(attrs={'class': 'form-control'}),
            'loja': forms.Select(attrs={'class': 'form-control'}),
            'centro_custo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Centro de custo'}),
        }

    def clean_nome(self):
        nome = self.cleaned_data['nome'].strip()
        loja = self.cleaned_data.get('loja')
        if Departamento.objects.filter(nome__iexact=nome, loja=loja).exists():
            raise forms.ValidationError("Já existe um departamento com este nome nesta loja.")
        return nome

    def clean_codigo(self):
        codigo = self.cleaned_data['codigo'].strip()
        if Departamento.objects.filter(codigo__iexact=codigo).exists():
            raise forms.ValidationError("Já existe um departamento com este código.")
        return codigo


class RegistroPontoForm(forms.ModelForm):
    class Meta:
        model = RegistroPonto
        fields = [
            'funcionario',
            'data_registro',
            'hora_registro',
            'tipo_registro',
            'loja',
            'ip_registro',
            'registro_manual',
            'justificativa',
            'aprovado_por',
            'observacoes',
        ]
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-control'}),
            'data_registro': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora_registro': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'tipo_registro': forms.Select(attrs={'class': 'form-control'}),
            'loja': forms.Select(attrs={'class': 'form-control'}),
            'ip_registro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'IP do registro'}),
            'registro_manual': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'justificativa': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Justificativa'}),
            'aprovado_por': forms.Select(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observações'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        registro_manual = cleaned_data.get('registro_manual')
        justificativa = cleaned_data.get('justificativa')

        if registro_manual and not justificativa:
            self.add_error('justificativa', "É obrigatório informar uma justificativa para registros manuais.")
        return cleaned_data


class JornadaTrabalhoForm(forms.ModelForm):
    class Meta:
        model = JornadaTrabalho
        fields = [
            'nome',
            'turno',
            'horario_entrada',
            'horario_saida',
            'horario_almoco_inicio',
            'horario_almoco_fim',
            'departamento',
            'loja',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da jornada'}),
            'turno': forms.Select(attrs={'class': 'form-control'}),
            'horario_entrada': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'horario_saida': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'horario_almoco_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'horario_almoco_fim': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'departamento': forms.Select(attrs={'class': 'form-control'}),
            'loja': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        entrada = cleaned_data.get('horario_entrada')
        saida = cleaned_data.get('horario_saida')
        almoco_inicio = cleaned_data.get('horario_almoco_inicio')
        almoco_fim = cleaned_data.get('horario_almoco_fim')

        if entrada and saida and saida <= entrada:
            self.add_error('horario_saida', "O horário de saída deve ser maior que o horário de entrada.")

        if (almoco_inicio and not almoco_fim) or (almoco_fim and not almoco_inicio):
            self.add_error('horario_almoco_fim', "Ambos os horários de almoço devem ser preenchidos ou deixados em branco.")

        if almoco_inicio and almoco_fim and almoco_fim <= almoco_inicio:
            self.add_error('horario_almoco_fim', "O horário de término do almoço deve ser maior que o início.")

        return cleaned_data


class PlanejarFeriasForm(forms.ModelForm):
    class Meta:
        model = Ferias
        # Selecionamos apenas os campos que o usuário deve preencher ao planejar férias
        fields = [
            'funcionario',
            'periodo_aquisitivo_inicio',
            'periodo_aquisitivo_fim',
            'data_inicio',
            'data_fim',
            'dias_ferias',
            'adiantamento_13',
            'observacoes',
        ]
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'periodo_aquisitivo_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'periodo_aquisitivo_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'dias_ferias': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'adiantamento_13': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': 0}),
            'observacoes': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        dias_ferias = cleaned_data.get('dias_ferias')

        # Validação básica de datas
        if data_inicio and data_fim and data_inicio > data_fim:
            self.add_error('data_fim', 'A data de fim deve ser maior ou igual à data de início.')

        # Validação de dias de férias
        if dias_ferias and data_inicio and data_fim:
            total_dias = (data_fim - data_inicio).days + 1
            if dias_ferias != total_dias:
                self.add_error('dias_ferias', f'Os dias de férias ({dias_ferias}) não correspondem ao período informado ({total_dias} dias).')



class ComunicadoForm(forms.ModelForm):
    class Meta:
        model = Comunicado
        fields = ["titulo", "mensagem"] 
        widgets = {
            "titulo": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Digite o título do comunicado",
            }),
            "mensagem": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Escreva a mensagem do comunicado",
            }),
        }
        labels = {
            "titulo": "Título",
            "mensagem": "Mensagem",
        }




