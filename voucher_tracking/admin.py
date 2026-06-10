from django.contrib import admin
from django.http import HttpResponse
from django.core.mail import EmailMessage
import openpyxl
import io
from collections import defaultdict
from .models import Voucher, EmailMaster

# 1. Purana Excel Export Button
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
    
    for voucher in queryset:
        worksheet.append([
            voucher.reference_no, str(voucher.payment_date) if voucher.payment_date else '',
            voucher.bank, voucher.cheque_no, voucher.beneficiary, float(voucher.required_amount),
            voucher.location, voucher.program, voucher.purpose or '', voucher.project or '',
            voucher.budget_head or '', str(voucher.approve_date) if voucher.approve_date else '',
            voucher.supporting or '', voucher.supporting_pending or '', "Yes" if voucher.payment_form_received else "No"
        ])
    workbook.save(response)
    return response


# 2. NAYA FEATURE: MANUALLY SEND REMINDER WITH EXCEL (ONLY FOR PENDING VOUCHERS)
@admin.action(description="Send Reminder Email with Excel (Only Pending)")
def send_voucher_reminder_action(modeladmin, request, queryset):
    # Sirf wahi vouchers filter karna jo received NAHI hue hain
    pending_vouchers = queryset.filter(payment_form_received=False)
    
    if not pending_vouchers.exists():
        modeladmin.message_user(request, "Error: Selected vouchers mein se koi bhi pending (Not Received) nahi hai!", level='warning')
        return
        
    # Vouchers ko Email ke hisab se group karna taaki ek vyakti ko ek hi mail jaye
    email_groups = defaultdict(list)
    for voucher in pending_vouchers:
        if voucher.to_email:
            email_groups[voucher.to_email].append(voucher)
            
    if not email_groups:
        modeladmin.message_user(request, "Error: Selected pending vouchers mein 'To Email' field khali hai!", level='warning')
        return

    emails_sent = 0

    # Har unique Email ke liye process chalu
    for to_email, vouchers in email_groups.items():
        # CC Emails ikthha karna
        cc_emails = list(set([v.cc_email for v in vouchers if v.cc_email]))
        
        # Memory ke andar Excel sheet banana (bina computer mein save kiye direct mail mein bhejne ke liye)
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = 'Pending Vouchers'
        
        headers = [
            'Reference No', 'Payment Date', 'Beneficiary', 'Required Amount', 
            'Location', 'Project', 'Budget Head', 'Supporting Pending'
        ]
        worksheet.append(headers)
        
        for v in vouchers:
            worksheet.append([
                v.reference_no, str(v.payment_date), v.beneficiary, 
                float(v.required_amount), v.location, v.project or '', 
                v.budget_head or '', v.supporting_pending or 'Pending'
            ])
            
        excel_file = io.BytesIO()
        workbook.save(excel_file)
        excel_file.seek(0)
        
        # Email Content taiyar karna
        subject = f"SPS Alert: Pending Vouchers Reminder"
        body = (
            f"Namaste,\n\n"
            f"Aapke reference/location se jude pending vouchers ki suchi is email ke saath attach ki gayi hai.\n"
            f"Kripya in vouchers ke pending supporting documents jald se jald jama karein.\n\n"
            f"• Total Pending Vouchers: {len(vouchers)}\n\n"
            f"Dhanyawad,\nSPS Voucher Tracking System"
        )
        
        # EmailMessage object banana taaki attachment bhej sakein
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=None,
            to=[to_email],
            cc=cc_emails
        )
        
        # Excel file ko attach karna
        email.attach('Pending_Vouchers_Report.xlsx', excel_file.read(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        email.send()
        emails_sent += 1

    modeladmin.message_user(request, f"Successfully {emails_sent} alag-alag vyaktiyon ko pending vouchers ka reminder Excel ke saath bhej diya gaya hai!")


# 3. Main Voucher Display Customization
@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    # Yeh list table mein column dikhayega
    list_display = (
        'reference_no', 'payment_date', 'beneficiary', 'required_amount', 
        'location', 'program', 'project', 'payment_form_received'
    )
    
    # TASK 2: Yeh line Reference No aur Beneficiary ke naam ko Link bana degi jisse click karke Edit kar sakein
    list_display_links = ('reference_no', 'beneficiary')
    
    # TASK 3 (Search): Yahan Name(beneficiary), Location, Program, aur Project se Search hoga
    search_fields = ('reference_no', 'beneficiary', 'location', 'program', 'project', 'to_email')
    
    # TASK 3 (Filter): Yeh side mein ek box banayega jahan se aap easily filter kar payenge
    list_filter = ('location', 'program', 'project', 'payment_form_received', 'payment_date')
    
    actions = [export_to_excel, send_voucher_reminder_action]

    # Auto Email logic jaisa tha wese hi hai
    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        
        if is_new:
            recipient_list = [emp.email for emp in EmailMaster.objects.all()]
            if recipient_list:
                subject = f"[AUTO-ALERT] Naya Voucher Add Hua: Ref-{obj.reference_no}"
                message = f"SPS System mein naya voucher aaya hai:\nRef: {obj.reference_no}\nAmount: Rs. {obj.required_amount}"
                
                from django.core.mail import send_mail
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=None,  
                    recipient_list=recipient_list,
                    fail_silently=False
                )
admin.site.register(EmailMaster)
# --- SVMS BRANDING ---
admin.site.site_header = "SPS Voucher Management System (SVMS)"
admin.site.site_title = "SVMS Admin Portal"
admin.site.index_title = "Welcome to SVMS Dashboard"