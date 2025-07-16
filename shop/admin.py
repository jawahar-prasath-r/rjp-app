from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'mobile', 'product', 'quantity', 'total_amount', 'payment_method', 'payment_status', 'paid', 'created_at']
    list_filter = ['product', 'payment_method', 'payment_status', 'paid', 'created_at']
    search_fields = ['name', 'mobile', 'product', 'transaction_id']
    readonly_fields = ['total_amount', 'created_at', 'updated_at']
    list_editable = ['payment_status', 'paid']
    ordering = ['-created_at']

    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'name', 'mobile', 'address')
        }),
        ('Order Details', {
            'fields': ('product', 'quantity', 'total_amount')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status', 'transaction_id', 'paid')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    actions = ['mark_as_paid', 'mark_as_completed', 'export_selected_orders']

    def mark_as_paid(self, request, queryset):
        updated = queryset.update(paid=True, payment_status='completed')
        self.message_user(request, f'{updated} orders marked as paid.')
    mark_as_paid.short_description = "Mark selected orders as paid"

    def mark_as_completed(self, request, queryset):
        updated = queryset.update(payment_status='completed')
        self.message_user(request, f'{updated} orders marked as completed.')
    mark_as_completed.short_description = "Mark selected orders as completed"

    def export_selected_orders(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="selected_orders.csv"'

        writer = csv.writer(response)
        writer.writerow(['Order ID', 'Customer Name', 'Mobile', 'Address', 'Product', 'Quantity', 'Total Amount', 'Payment Method', 'Payment Status', 'Paid', 'Created At'])

        for order in queryset:
            writer.writerow([
                order.id, order.name, order.mobile, order.address,
                order.get_product_display(), order.quantity, order.total_amount,
                order.get_payment_method_display(), order.get_payment_status_display(),
                'Yes' if order.paid else 'No', order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

        return response
    export_selected_orders.short_description = "Export selected orders to CSV"

# Customize admin site header
admin.site.site_header = "JP Dry Fish Admin"
admin.site.site_title = "JP Dry Fish Admin Portal"
admin.site.index_title = "Welcome to JP Dry Fish Administration"
