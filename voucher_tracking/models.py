from django.db import models

# 1. Yeh sirf Reference ki jankari rakhega
class VoucherReference(models.Model):
    reference_number = models.CharField(max_length=100, unique=True, verbose_name="Reference Number")
    payment_date = models.DateField(verbose_name="Payment Date")
    approve_date = models.DateField(verbose_name="Approve Date")

    def __str__(self):
        return self.reference_number

# 2. Yeh har ek Beneficiary ki alag jankari rakhega
class VoucherBeneficiary(models.Model):
    # Is line se yeh upar wale Reference se jud jayega
    voucher_reference = models.ForeignKey(VoucherReference, on_delete=models.CASCADE, related_name='beneficiaries')
    
    # Har beneficiary ki apni alag fields
    beneficiary_name = models.CharField(max_length=255, verbose_name="Beneficiary Name")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Amount")
    description = models.TextField(verbose_name="Description", blank=True, null=True)
    # Agar koi aur field bhi dobara bharni ho (jaise Account No), toh wo yahan jod sakte hain

    def __str__(self):
        return f"{self.beneficiary_name} - {self.amount}"
