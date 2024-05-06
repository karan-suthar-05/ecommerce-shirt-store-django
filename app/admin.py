from django.contrib import admin
from .models import *
from django.core.mail import send_mail
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from django.urls import path
from django.shortcuts import render,redirect,HttpResponse
from django.urls import reverse
from .views import generate_report
from .views import customer_report

# cart
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_price')
    readonly_fields = ('user', 'total_price')

    def has_add_permission(self, request):
        return False  # Disallow adding new Cart instances

    def has_delete_permission(self, request, obj=None):
        return False  # Disallow deleting Cart instances

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return []  # Allow all fields to be editable for superusers
        else:
            return self.readonly_fields  # Make fields read-only for non-superusers

admin.site.register(Cart, CartAdmin)

#order item inline class

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ('product', 'quantity', 'subtotal')
    readonly_fields = ('subtotal','product', 'quantity')
    extra = 0
    
    def has_add_permission(self, request, obj=None):
        return False  # Disallow adding new Cart instances

    def has_delete_permission(self, request, obj=None):
        return False  # Disallow deleting Cart instances


# order

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','user_name','user_contact', 'order_status', 'total_price', 'billing_address_display')
    readonly_fields = ('user', 'payment_method','total_price', 'billing_address','is_cancelled' , 'razorpay_order_id', 'razorpay_payment_id', 'created_at', 'updated_at')
    list_filter = ('payment_method', 'is_cancelled', 'is_refunded', 'order_status',)
    search_fields = ('user__user_fname','user__user_lname', 'total_price', 'payment_method', 'billing_address__fname', 'billing_address__lname', 'billing_address__email', 'billing_address__contact', 'billing_address__house_street', 'billing_address__apartment_area', 'billing_address__city', 'billing_address__state', 'billing_address__pincode', 'razorpay_order_id', 'razorpay_payment_id', 'order_status', 'is_cancelled', 'is_refunded', 'created_at', 'updated_at')
    inlines = [OrderItemInline]

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('generate_report/',self.admin_site.admin_view(self.generate_report),name='myapp_sales_report')
        ]
        return my_urls + urls
    
    def generate_report(self,request):
        if request.method == "POST":
            date_range = request.POST.get('date_range')
            return generate_report(request,date_range)
        else:
            return redirect(reverse('admin:myapp_sales_report'))


    def user_name(self, obj):
        return obj.user.user_fname + " " + obj.user.user_lname
    user_name.short_description = 'User Name'

    def user_contact(self, obj):
        return obj.user.user_contact
    user_contact.short_description = 'User Contact'

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'order_status':
            kwargs['choices'] = [choice for choice in Order.ORDER_STATUS if choice[0] != 'cancelled']
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj=obj)
        if obj and not obj.is_cancelled:
            for fieldset in fieldsets:
                fields = fieldset[1]['fields']
                if 'is_refunded' in fields:
                    fields.remove('is_refunded')
        return fieldsets 

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_cancelled:
            return self.readonly_fields + ('order_status',)
        return self.readonly_fields

    def billing_address_display(self, obj):
        if obj.billing_address:
            return f"{obj.billing_address.fname} {obj.billing_address.lname}, {obj.billing_address.house_street}, {obj.billing_address.city}, {obj.billing_address.state}, {obj.billing_address.pincode}"
        return "N/A"
    billing_address_display.short_description = "Billing Address"
    
    # def download_data(self,request):
    #     # Fetching delivered orders
    #     delivered_orders = Order.objects.filter(order_status='delivered')
    #     total_del_orders = delivered_orders.count()
    #     # Calculating total revenue from delivered orders
    #     total_revenue = sum(order.total_price for order in delivered_orders)
    #     average_order_value = total_revenue / total_del_orders if total_del_orders != 0 else 0

    #     # Fetching all orders
    #     all_orders = Order.objects.all()

    #     # Initializing variables to store summary statistics
    #     total_orders = all_orders.count()

    #     order_status_counts = defaultdict(int)
    #     for order in all_orders:
    #         order_status_counts[order.order_status] += 1

    #     # Fetching order items and associated products for all orders
    #     order_details = []
        

    #     for order in all_orders:
    #         order_details.append({
    #             'order_id': order.id,
    #             'order_date': order.created_at,
    #             'order_status': order.order_status,
    #             'total_price': order.total_price
    #         })
            

    #     # Generating the PDF report
    #     response = HttpResponse(content_type='application/pdf')
    #     response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'

    #     doc = SimpleDocTemplate(response, pagesize=letter)
    #     styles = getSampleStyleSheet()
    #     elements = []

    #     # Add Sales Report title and date
    #     elements.append(Paragraph('Sales Report', styles['Title']))
    #     # Add date here

    #     # Add Summary Statistics
    #     elements.append(Paragraph('Summary Statistics', styles['Heading2']))
    #     summary_table_data = [
    #         ['Total Number of Orders:', total_orders],
    #         ['Total Sales Revenue:', total_revenue],
    #         ['Average Order Value:', average_order_value],
    #         ['Number of Orders by Status:'] + [f'{status}: {count}' for status, count in order_status_counts.items()]
    #     ]
    #     summary_table = Table(summary_table_data, colWidths=[200, '*'])
    #     summary_table.setStyle(TableStyle([
    #         ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
    #         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    #         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    #         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    #         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    #         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    #     ]))
    #     elements.append(summary_table)

    #     # Add Order Details
    #     elements.append(Paragraph('Order Details', styles['Heading2']))
    #     order_details_data = [['Order ID', 'Order Date', 'Order Status', 'Total Price']] + \
    #                         [[order['order_id'], order['order_date'], order['order_status'], order['total_price']] for order in order_details]
    #     order_details_table = Table(order_details_data)
    #     order_details_table.setStyle(TableStyle([
    #         ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
    #         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    #         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    #         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    #         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    #         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    #     ]))
    #     elements.append(order_details_table)

    #     doc.build(elements)

    #     return response

    # def get_urls(self):
    #     urls = super().get_urls()
    #     order_url = [path('report/',self.download_data),]
    #     return order_url + urls

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(Order, OrderAdmin)

# order-items

# class OrderItemAdmin(admin.ModelAdmin):
#     list_display = ('order', 'product', 'quantity', 'subtotal')
#     search_fields = ('order__id', 'product__product_name', 'quantity')
#     list_filter = ('product__product_name',)  # Filter based on product category
#     # raw_id_fields = ('product',)  # Display product field as a search input

#     def subtotal(self, obj):
#         if obj.product.discount_price == 0:
#             return obj.product.price * obj.quantity
#         else:
#             return obj.product.discount_price * obj.quantity
#     subtotal.short_description = 'Subtotal'  # Set the column header name for the subtotal

#     def has_add_permission(self, request):
#         return False  # Disallow adding new Cart instances

#     def has_delete_permission(self, request, obj=None):
#         return False  # Disallow deleting Cart instances

# admin.site.register(OrderItem, OrderItemAdmin)



class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('email', 'message', 'admin_response')
    list_filter = ('created_at',)
    search_fields = ('name', 'email', 'message')


    def save_model(self, request, obj, form, change):
        if obj.admin_response:
            # If admin response is provided, send an email to the user
            send_mail(
                subject='Response to your query',
                message="From STYLE-X shirts : \n\n" + obj.admin_response,
                from_email=None,  # Add your email address here
                recipient_list=[obj.email],
                fail_silently=True,
            )
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        # Make all fields read-only except admin_response
        if obj:
            return [field.name for field in obj._meta.fields if field.name != 'admin_response']
        return self.readonly_fields
    
    def has_add_permission(self, request):
        # Disable the "Add" button
        return False

admin.site.register(ContactMessage, ContactMessageAdmin)


# from .models import Product, Product_image

class Product_imageInline(admin.TabularInline):  # or admin.StackedInline for a vertical display
    model = Product_image
    extra = 1  # Set to 1 or more depending on how many images you want to add

class ProductAdmin(admin.ModelAdmin):
    inlines = [Product_imageInline]
    list_display = ['product_name','category','sizes','stock_quantity']
    list_filter = ['category','sizes','material']
    readonly_fields = ('discount_price',) 

    def save_model(self, request, obj, form, change):
    # Call the parent class's save_model method to save the object
        super().save_model(request, obj, form, change)

        # Calculate the discount price if an offer is selected
        if obj.offer:
            discount_price = obj.price - (obj.price * (obj.offer.discount_percentage / 100))
            obj.discount_price = discount_price
        else:
            obj.discount_price =0
        obj.save()

admin.site.register(Product, ProductAdmin)


class ProductionAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'production_date','production_cost','notes')
    list_filter = ('production_date',)
    search_fields = ('product', 'quantity', 'production_date','production_cost','notes')

    
    def download_data(self, request):
        all_production = Production.objects.all()

        # Calculating summary statistics
        total_products_produced = all_production.count()
        total_production_cost_based_on_quantity = sum(production.quantity * production.production_cost for production in all_production)

        # Fetching product-wise production details
        production_details = []
        for production in all_production:
            product = production.product
            subtotal = production.quantity * production.production_cost
            production_details.append({
                'product_name': product.product_name,
                'quantity': production.quantity,
                'product_price': product.price,
                'production_cost': production.production_cost,
                'subtotal': subtotal,
                'production_date': production.production_date.strftime('%Y-%m-%d')  # Format the date as desired
            })

        # Generating the PDF report
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="production_report.pdf"'

        doc = SimpleDocTemplate(response, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Add Production Report title
        elements.append(Paragraph('Production Report', styles['Title']))

        # Add Summary Statistics
        elements.append(Paragraph('Summary Statistics', styles['Heading2']))
        summary_table_data = [
            ['Total Products Produced:', total_products_produced],
            ['Total Production Cost Based on Quantity:', total_production_cost_based_on_quantity],
        ]
        summary_table = Table(summary_table_data, colWidths=[200, '*'])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ]))
        elements.append(summary_table)

        # Add Product-wise Production Details
        elements.append(Paragraph('Product-wise Production Details', styles['Heading2']))
        production_details_data = [['Product Name', 'Quantity Produced', 'Product Price', 'Production Cost', 'Subtotal', 'Production Date']] + \
                                [[p['product_name'], p['quantity'], p['product_price'], p['production_cost'], p['subtotal'], p['production_date']] for p in production_details]
        production_details_table = Table(production_details_data)
        production_details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ]))
        elements.append(production_details_table)

        doc.build(elements)

        return response

    def get_urls(self):
        urls = super().get_urls()
        order_url = [path('report/',self.download_data),]
        return order_url + urls

admin.site.register(Production, ProductionAdmin)

# user
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_fname','user_lname','user_contact','user_email')
    exclude = ('role_id',) 

    def get_readonly_fields(self, request, obj=None):
        # Make all fields read-only except admin_response
        if obj:
            return [field.name for field in obj._meta.fields if field.name != 'role_id']
        return self.readonly_fields
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('customer_report/',self.admin_site.admin_view(self.customer_report),name='myapp_customer_report')
        ]
        return my_urls + urls
    
    def customer_report(self,request):
        if request.method == "POST":
            date_range = request.POST.get('date_range')
            return customer_report(request,date_range)
        else:
            return redirect(reverse('admin:myapp_customer_report'))

admin.site.register(User, UserAdmin)



# Register your models here.
admin.site.register(State)
admin.site.register(City)
admin.site.register(Area)
admin.site.register(Company)
# admin.site.register(Role)
# admin.site.register(User)
# admin.site.register(Product)
admin.site.register(Product_category)
admin.site.register(CollectionTag)
admin.site.register(Product_size)
admin.site.register(Product_color)
admin.site.register(Product_material)
# admin.site.register(Product_image)
# admin.site.register(Production)
admin.site.register(Offer)
# admin.site.register(Cart_item)
# admin.site.register(Order)
# admin.site.register(OrderItem)
# admin.site.register(BillingAddress)