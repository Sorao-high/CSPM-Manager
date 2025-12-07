from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView # 追加
from django.urls import reverse_lazy
from django.db.models import Count, Q, Prefetch  # Prefetch を追加
from django.db.models import Count, Q
from .models import CloudAccount, Department, MonitorGroup
from .forms import CloudAccountForm, MonitorGroupForm, CloudAccountEditForm # 追加
import json

from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from datetime import datetime
from django.utils.dateparse import parse_date

class DashboardView(TemplateView):
    template_name = "management/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # --- 1. 期間フィルタの取得 ---
        start_param = self.request.GET.get('start')
        end_param = self.request.GET.get('end')
        
        # フィルタリング用のベースクエリ (デフォルトは全件)
        account_qs = CloudAccount.objects.all()
        
        # 期間指定がある場合、request_date で絞り込み
        if start_param and end_param:
            account_qs = account_qs.filter(
                request_date__range=[start_param, end_param]
            )
        
        # フォームに値を残すためにコンテキストに渡す
        context['start_date'] = start_param
        context['end_date'] = end_param
        context['is_filtered'] = bool(start_param and end_param)

        # --- 2. KPI集計 (フィルタ済みQSを使用) ---
        context['total_depts'] = Department.objects.count() # マスタなのでフィルタしない
        context['total_groups'] = MonitorGroup.objects.count() # マスタなのでフィルタしない
        
        # アカウント関連はフィルタ結果に基づく
        context['total_accounts'] = account_qs.count()
        context['connected_accounts'] = account_qs.filter(status='Connected').count()
        
        # --- 3. プロバイダ別内訳 (フィルタ済みQSを使用) ---
        provider_data = account_qs.values('provider').annotate(count=Count('id'))
        context['provider_counts'] = provider_data
        context['chart_labels'] = json.dumps([d['provider'] for d in provider_data])
        context['chart_data'] = json.dumps([d['count'] for d in provider_data])

        # --- 4. 接続推移グラフ (フィルタ期間に合わせて再集計) ---
        # 接続推移は request_date ではなく connection_date を見るのが自然
        trend_qs = CloudAccount.objects.exclude(connection_date__isnull=True)
        
        if start_param and end_param:
            # 期間指定があればその期間で
            trend_qs = trend_qs.filter(connection_date__range=[start_param, end_param])
        else:
            # 指定がなければ「全期間」とするため、何もしない
            pass

        monthly_stats = (
            trend_qs
            .annotate(month=TruncMonth('connection_date'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        
        history_labels = [item['month'].strftime('%Y-%m') for item in monthly_stats]
        history_data = [item['count'] for item in monthly_stats]
        
        context['history_labels'] = json.dumps(history_labels)
        context['history_data'] = json.dumps(history_data)

        # --- 5. その他のリスト (フィルタ済みQSを使用) ---
        # 要対応リスト
        context['attention_accounts'] = account_qs.exclude(status='Connected')[:5]

        # 部署ランキング (フィルタ期間内のアカウント数でランク付け)
        # ※ここだけ少し複雑ですが、account_qsを使って集計します
        dept_ranking = (
            Department.objects
            .filter(monitorgroup__cloudaccount__in=account_qs) # フィルタ対象のアカウントを持つ部署のみ
            .annotate(acc_count=Count('monitorgroup__cloudaccount', filter=Q(monitorgroup__cloudaccount__in=account_qs)))
            .order_by('-acc_count')[:5]
        )
        context['dept_ranking'] = dept_ranking

        return context

class AccountListView(ListView):
    model = Department
    template_name = "management/account_list.html"
    context_object_name = "departments"

    def get_queryset(self):
        qs = Department.objects.all()
        q_word = self.request.GET.get('q')

        if q_word:
            # === 検索モード ===
            
            # 1. 検索ヒットした「アカウント」を探す
            account_matches = CloudAccount.objects.filter(
                Q(name__icontains=q_word) | 
                Q(account_id__icontains=q_word) |
                Q(provider__icontains=q_word)
            )
            
            # 2. 検索ヒットした「監視グループ」を探す
            group_name_matches = MonitorGroup.objects.filter(name__icontains=q_word)
            
            # 3. 最終的に表示すべき「アカウント」を決める
            # (直接ヒットしたアカウント OR ヒットしたグループに属する全アカウント)
            final_account_qs = CloudAccount.objects.filter(
                Q(id__in=account_matches) | 
                Q(monitor_group__in=group_name_matches)
            )

            # 4. 最終的に表示すべき「監視グループ」を決める
            # (名前がヒットしたグループ OR ヒットしたアカウントを持っているグループ)
            # 並且、そのグループの中身(cloudaccount_set)は上記3で絞り込んだものだけロードする
            final_group_qs = MonitorGroup.objects.filter(
                Q(id__in=group_name_matches) |
                Q(cloudaccount__in=account_matches)
            ).distinct().prefetch_related(
                Prefetch('cloudaccount_set', queryset=final_account_qs)
            )

            # 5. 部署を絞り込む
            # (表示すべきグループを持っている部署だけ)
            qs = qs.filter(monitorgroup__in=final_group_qs).distinct().prefetch_related(
                Prefetch('monitorgroup_set', queryset=final_group_qs)
            )
            
        else:
            # === 通常モード（全件） ===
            qs = qs.prefetch_related('monitorgroup_set__cloudaccount_set')
            
        return qs

class AccountCreateView(CreateView):
    model = CloudAccount
    form_class = CloudAccountForm
    template_name = "management/account_form.html"
    success_url = reverse_lazy('account_list')

    def form_valid(self, form):
        dept_name = form.cleaned_data['department_name']
        group_name = form.cleaned_data['monitor_group_name']
        # ▼▼▼ 追加: 入力されたIDを取得 ▼▼▼
        group_id_input = form.cleaned_data['monitor_group_id']
        
        department, _ = Department.objects.get_or_create(
            name=dept_name
        )
        
        monitor_group, created = MonitorGroup.objects.get_or_create(
            name=group_name,
            department=department,
            defaults={
                'group_id': group_id_input, # ▼▼▼ 新規作成時、IDを保存 ▼▼▼
                'responsible_contact': '未設定',
                'alert_email': '未設定',
                'report_email': '未設定'
            }
        )
        
        form.instance.monitor_group = monitor_group
        return super().form_valid(form)

# === 監視グループ操作 ===
class MonitorGroupUpdateView(UpdateView):
    model = MonitorGroup
    form_class = MonitorGroupForm
    template_name = "management/monitor_group_form.html"
    success_url = reverse_lazy('account_list')

class MonitorGroupDeleteView(DeleteView):
    model = MonitorGroup
    template_name = "management/delete_confirm.html" # 共通の削除確認画面
    success_url = reverse_lazy('account_list')

# === アカウント操作 ===
class CloudAccountUpdateView(UpdateView):
    model = CloudAccount
    form_class = CloudAccountEditForm
    template_name = "management/account_form.html" # 既存のフォームHTMLを再利用
    success_url = reverse_lazy('account_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True # 編集モードであることをテンプレートに伝える
        return context

class CloudAccountDeleteView(DeleteView):
    model = CloudAccount
    template_name = "management/delete_confirm.html" # 共通の削除確認画面
    success_url = reverse_lazy('account_list')