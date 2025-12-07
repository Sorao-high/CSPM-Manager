from django.db import models

class Department(models.Model):
    name = models.CharField("部署名", max_length=100)
    memo = models.TextField("備考", blank=True)
    def __str__(self): return self.name

class MonitorGroup(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="申請部署")
    name = models.CharField("監視グループ名", max_length=100)
    group_id = models.CharField("監視グループID", max_length=50, null=True, blank=True)
    responsible_contact = models.TextField("責任者連絡先", help_text="カンマ区切り")
    cc_contact = models.TextField("CC用連絡先", blank=True)
    alert_email = models.TextField("アラート通知先")
    report_email = models.TextField("レポート送付先")
    memo = models.TextField("備考", blank=True)
    def __str__(self): return f"{self.name} ({self.department.name})"

class CloudAccount(models.Model):
    class Provider(models.TextChoices):
        AWS = 'AWS', 'AWS'
        AZURE = 'Azure', 'Azure'
        GCP = 'GCP', 'Google Cloud'
        OCI = 'OCI', 'Oracle Cloud'
        OTHER = 'Other', 'その他'

    class Status(models.TextChoices):
        WAITING = 'Waiting', '未接続'
        CONNECTED = 'Connected', '接続済み'
        DISCONNECTED = 'Disconnected', '解除済み'

    monitor_group = models.ForeignKey(MonitorGroup, on_delete=models.CASCADE, verbose_name="監視グループ")
    name = models.CharField("アカウント名", max_length=100)
    provider = models.CharField("種別", max_length=20, choices=Provider.choices)
    account_id = models.CharField("アカウントID", max_length=100, unique=True)
    request_date = models.DateField("依頼日", null=True, blank=True)
    connection_date = models.DateField("接続日", null=True, blank=True)
    status = models.CharField("状態", max_length=20, choices=Status.choices, default=Status.WAITING)

    def __str__(self): return f"[{self.provider}] {self.name}"