from django.db import models

class EmailMaster(models.Model):
    email = models.EmailField()
    name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.email

class Voucher(models.Model):
    reference_no = models.CharField(max_length=50, unique=True)
    payment_date = models.DateField()
    bank = models.CharField(max_length=100)
    cheque_no = models.CharField(max_length=50, blank=True, null=True)
    beneficiary = models.CharField(max_length=200)
    required_amount = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=100)
    program = models.CharField(max_length=100)
    payment_form_received = models.BooleanField(default=False)
    purpose = models.TextField(blank=True, null=True)
    project = models.CharField(max_length=100, blank=True, null=True)
    budget_head = models.CharField(max_length=100, blank=True, null=True)
    approve_date = models.DateField(blank=True, null=True)
    supporting = models.CharField(max_length=200, blank=True, null=True)
    supporting_pending = models.TextField(blank=True, null=True)
    
    # ---- REMINDER KE LIYE NAYE EMAIL FIELDS ----
    to_email = models.EmailField(blank=True, null=True, help_text="Jis person ko reminder bhejna hai")
    cc_email = models.EmailField(blank=True, null=True, help_text="CC mein rakhne ke liye email (Optional)")

    def __str__(self):
        return f"{self.reference_no} - {self.beneficiary}"
