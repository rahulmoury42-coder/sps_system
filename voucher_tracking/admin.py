from django.contrib import admin
from django.http import HttpResponse
from django.core.mail import EmailMessage, send_mail
import openpyxl
import io
from collections import defaultdict
from .models import VoucherReference, VoucherBeneficiary, EmailMaster

# Beneficiary ko Table ke roop mein dikhane ke liye
class VoucherBeneficiaryInline(admin.TabularInline):
    model = VoucherBeneficiary
    extra = 1  # Shuruat mein 1 khali row dikhega
    min_num = 1 # Kam se kam 1 beneficiary zaroori hai
    
    # Is line se columns ka order set hoga, Budget Head ekdum last mein dikhega
    fields = ['beneficiary', 'required_amount', 'purpose', 'supporting', 'supporting_pending', 'budget_head']

# 1. Purana Excel Export Button (Naye Structure ke hisab se updated)
@admin.action(description="Download Selected as Excel")
def export_to_excel(modeladmin, request, queryset):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="SPS_Vouchers_Report.xlsx"'
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Vouchers Data'
    
    headers = [
        'Reference No', 'Payment Date', 'Bank', 'Cheque No', 'Beneficiary', 
        'Required Amount', 'Location', 'Program', 'Purpose', 'Project', 
        'Budget Head', 'Approve Date', 'Supporting Docs', 'Supporting Pending', 'Payment Form Received'
    ]
    worksheet.append(headers)
    
    for ref in queryset:
        # Har reference ke andar ke saare beneficiaries ko nikal kar row banana
        for b in ref.beneficiaries.all():
            worksheet.append([
                ref.reference_no, str(ref.payment_date) if ref.payment_date else '',
                ref.bank or '', ref.cheque_no or '', b.beneficiary, float(b.required_amount),
                ref.location, ref.program, b.purpose or '', ref.project or '',
                b.budget_head or '', str(ref.approve_date) if ref.approve_date else '',
                b.supporting or '', b.supporting_pending or '', "Yes" if ref.payment_form_received else "No"
            ])
    workbook.save(response)
    return response


# 2. Purana Manual Reminder Action (Naye Structure ke hisab se updated)
@admin.action(description="Send Reminder Email with Excel (Only Pending)")
def send_voucher_reminder_action(modeladmin, request, queryset):
    pending_vouchers = queryset.filter(payment_form_received=False)
    
    if not pending_vouchers.exists():
        modeladmin.message_user(request, "Error: Selected vouchers mein se koi bhi pending (Not Received) nahi hai!", level='warning')
        return
        
    email_groups = defaultdict(list)
    for ref in pending_vouchers:
        if ref.to_email:
            email_groups[ref.to_email].append(ref)
            
    if not email_groups:
        modeladmin.message_user(request, "Error: Selected pending vouchers mein 'To Email' field khali hai!", level='warning')
        return

    emails_sent = 0

    for to_email, refs in email_groups.items():
        cc_emails = list(set([r.cc_email for r in refs if r.cc_email]))
        
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = 'Pending Vouchers'
        
        headers = [
            'Reference No', 'Payment Date', 'Beneficiary', 'Required Amount', 
            'Location', 'Project', 'Budget Head', 'Supporting Pending'
        ]
        worksheet.append(headers)
        
        for ref in refs:
            for b in ref.beneficiaries.all():
                worksheet.append([
                    ref.reference_no, str(ref.payment_date), b.beneficiary, 
                    float(b.required_amount), ref.location, ref.project or '', 
                    b.budget_head or '', b.supporting_pending or 'Pending'
                ])
                
        excel_file = io.BytesIO()
        workbook.save(excel_file)
        excel_file.seek(0)
        
        total_beneficiaries = sum([ref.beneficiaries.count() for ref in refs])
        subject = f"SPS Alert: Pending Vouchers Reminder"
        body = (
            f"Namaste,\n\n"
            f"Aapke reference/location se jude pending vouchers ki suchi is email ke saath attach ki gayi hai.\n"
            f"Kripya in vouchers ke pending supporting documents jald se jald jama karein.\n\n"
            f"• Total Pending References: {len(refs)}\n"
            f"• Total Pending Entries: {total_beneficiaries}\n\n"
            f"Dhanyawad,\nSPS Voucher Tracking System"
        )
        
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=None,
            to=[to_email],
            cc=cc_emails
        )
        
        email.attach('Pending_Vouchers_Report.xlsx', excel_file.read(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        email.send()
        emails_sent += 1

    modeladmin.message_user(request, f"Successfully {emails_sent} alag-alag vyaktiyon ko pending vouchers ka reminder Excel ke saath bhej diya gaya hai!")


# 3. Main Voucher Display Customization
@admin.register(VoucherReference)
class VoucherReferenceAdmin(admin.ModelAdmin):
    list_display = (
        'reference_no', 'payment_date', 'location', 'program', 'project', 'payment_form_received'
    )
    list_display_links = ('reference_no',)
    search_fields = ('reference_no', 'location', 'program', 'project', 'to_email')
    list_filter = ('location', 'program', 'project', 'payment_form_received', 'payment_date')
    actions = [export_to_excel, send_voucher_reminder_action]
    
    # Is line se Beneficiary ka form Reference ke andar hi khul jayega
    inlines = [VoucherBeneficiaryInline]

    # Auto Email logic jaisa tha wese hi hai (Bina crash kiye chalega)
    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        
        if is_new:
            recipient_list = [emp.email for emp in EmailMaster.objects.all()]
            if recipient_list:
                subject = f"[AUTO-ALERT] Naya Voucher Add Hua: Ref-{obj.reference_no}"
                message = f"SPS System mein naya voucher aaya hai:\nRef: {obj.reference_no}\nLocation: {obj.location}"
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=None,  
                    recipient_list=recipient_list,
                    fail_silently=True
                )

admin.site.register(EmailMaster)

# --- SVMS BRANDING ---
admin.site.site_header = "SPS Voucher Management System (SVMS)"
admin.site.site_title = "SVMS Admin Portal"
admin.site.index_title = "Welcome to SVMS Dashboard"
