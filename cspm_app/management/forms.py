from django import forms
from .models import CloudAccount, MonitorGroup

class CloudAccountForm(forms.ModelForm):
    # --- 追加: フォームだけで使う入力欄 ---
    department_name = forms.CharField(
        label="申請部署名",
        max_length=100,
        help_text="部署名を入力（既存なら紐付け、なければ新規作成されます）"
    )
    monitor_group_name = forms.CharField(
        label="監視グループ名",
        max_length=100,
        help_text="グループ名を入力（既存なら紐付け、なければ新規作成されます）"
    )

    monitor_group_id = forms.CharField(
        label="監視グループID",
        max_length=50,
        required=False, # 必須にはしない（既存グループへの紐付け時など）
        help_text="新規作成時に入力（任意）"
    )

    class Meta:
        model = CloudAccount
        # ▼▼▼ fieldsの順番を調整（monitor_group_idを追加） ▼▼▼
        fields = ['department_name', 'monitor_group_name', 'monitor_group_id', 'name', 'provider', 'account_id', 'request_date', 'connection_date', 'status']
        widgets = {
            'request_date': forms.DateInput(attrs={'type': 'date'}),
            'connection_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # デザインスタイルの適用
        common_style = "w-full bg-slate-900 border border-slate-700 text-cyan px-4 py-3 focus:outline-none focus:border-cyan focus:shadow-[0_0_10px_rgba(69,243,255,0.2)] font-mono text-sm placeholder-slate-600 transition-colors"
        
        for field in self.fields.values():
            field.widget.attrs['class'] = common_style
            
        # Selectボックス(プルダウン)だけスタイル調整
        self.fields['provider'].widget.attrs['class'] += " appearance-none"
        self.fields['status'].widget.attrs['class'] += " appearance-none"
        
        # ★ここがポイント: monitor_group の行は削除済みです

class MonitorGroupForm(forms.ModelForm):
    """監視グループ編集用フォーム"""
    class Meta:
        model = MonitorGroup
        # ▼▼▼ fieldsに 'group_id' を追加 ▼▼▼
        fields = ['name', 'group_id', 'responsible_contact', 'cc_contact', 'alert_email', 'report_email', 'memo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        common_style = "w-full bg-slate-900 border border-slate-700 text-cyan px-4 py-3 focus:outline-none focus:border-cyan focus:shadow-[0_0_10px_rgba(69,243,255,0.2)] font-mono text-sm placeholder-slate-600 transition-colors"
        for field in self.fields.values():
            field.widget.attrs['class'] = common_style

class CloudAccountEditForm(forms.ModelForm):
    """アカウント編集用フォーム（所属部署の移動などは除外）"""
    class Meta:
        model = CloudAccount
        fields = ['name', 'provider', 'account_id', 'request_date', 'connection_date', 'status']
        widgets = {
            'request_date': forms.DateInput(attrs={'type': 'date'}),
            'connection_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        common_style = "w-full bg-slate-900 border border-slate-700 text-cyan px-4 py-3 focus:outline-none focus:border-cyan focus:shadow-[0_0_10px_rgba(69,243,255,0.2)] font-mono text-sm placeholder-slate-600 transition-colors"
        for field in self.fields.values():
            field.widget.attrs['class'] = common_style
        
        self.fields['provider'].widget.attrs['class'] += " appearance-none"
        self.fields['status'].widget.attrs['class'] += " appearance-none"