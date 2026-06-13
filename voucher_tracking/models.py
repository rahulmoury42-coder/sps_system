from django.db import models

class EmailMaster(models.Model):
    name = models.CharField(max_length=100, verbose_name="Employee Name")
    email = models.EmailField(unique=True, verbose_name="Email Address")

    def __str__(self):
        return f"{self.name} ({self.email})"


# 1. Yeh sirf Reference aur Master jankari save karega (Ek baar bhari jayegi)
class VoucherReference(models.Model):
    reference_no = models.CharField(max_length=100, unique=True, verbose_name="Reference No")
    payment_date = models.DateField(verbose_name="Payment Date", blank=True, null=True)
    bank = models.CharField(max_length=100, verbose_name="Bank", blank=True, null=True)
    cheque_no = models.CharField(max_length=100, verbose_name="Cheque No", blank=True, null=True)
    location = models.CharField(max_length=100, verbose_name="Location")
    program = models.CharField(max_length=100, verbose_name="Program")
    project = models.CharField(max_length=100, verbose_name="Project", blank=True, null=True)
    approve_date = models.DateField(verbose_name="Approve Date", blank=True, null=True)
    payment_form_received = models.BooleanField(default=False, verbose_name="Payment Form Received")
    to_email = models.EmailField(verbose_name="To Email", blank=True, null=True)
    cc_email = models.EmailField(verbose_name="CC Email", blank=True, null=True)

    def __str__(self):
        return self.reference_no


# 2. Yeh har ek Reference ke andar jitne chahein utne Beneficiaries add karne dega
class VoucherBeneficiary(models.Model):
    voucher_reference = models.ForeignKey(VoucherReference, on_delete=models.CASCADE, related_name='beneficiaries')
    beneficiary = models.CharField(max_length=255, verbose_name="Beneficiary")
    required_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Required Amount")
    purpose = models.TextField(verbose_name="Purpose", blank=True, null=True)
    budget_head = models.CharField(max_length=100, verbose_name="Budget Head", blank=True, null=True)
    supporting = models.CharField(max_length=255, verbose_name="Supporting Docs", blank=True, null=True)
    supporting_pending = models.CharField(max_length=255, verbose_name="Supporting Pending", blank=True, null=True)

    def __str__(self):
        return f"{self.beneficiary} ({self.required_amount})"
