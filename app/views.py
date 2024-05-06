from django.shortcuts import render,redirect,HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import *
from random import randint
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password,check_password
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from datetime import datetime
from django.utils.timezone import now
import razorpay
from stylex.settings import RAZORPAY_API_KEY,RAZORPAY_SECRET_KEY
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from io import BytesIO


from xhtml2pdf import pisa
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone

# def fetch_records(start_date, end_date):
#     records = Order.objects.filter(created_at__range=[start_date, end_date])
#     return records

def get_shop_info():
    shop = Company.objects.first()
    return shop

from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa
from .models import Order, Product, Product_category
from django.db.models import Sum, Value,Count
from django.db.models.functions import Coalesce
from django.db.models import Case, F, Sum, DecimalField, Value, When
from datetime import date
from collections import defaultdict

def calculate_age(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def customer_report(request, date_range):
    time_periods = {
        'today': (timezone.now().date(), timezone.now().date()),
        'last_7_days': (timezone.now().date() - timezone.timedelta(days=7), timezone.now().date()),
        'this_month': (timezone.now().replace(day=1).date(), timezone.now().date()),
        'last_month': ((timezone.now().replace(day=1) - timezone.timedelta(days=1)).replace(day=1).date(), (timezone.now().replace(day=1) - timezone.timedelta(days=1)).date()),
        'this_year': (timezone.now().replace(month=1, day=1).date(), timezone.now().date()),
    }

    # Get start and end dates based on the selected date range
    start_date, end_date = time_periods[date_range]

    # Fetch relevant data from the database
    orders = Order.objects.filter(
        created_at__range=[start_date, end_date]
    ).exclude(order_status='cancelled')
    # Fetch data from the database based on the date range or any other criteria
    users = User.objects.all()  # Example: Fetch all users
    total_users = users.count()

    age_ranges = {
        'under_18': users.filter(dob__gt=date.today().replace(year=date.today().year - 18)).count(),
        '18_24': users.filter(dob__year__gte=date.today().year - 24, dob__year__lte=date.today().year - 18).count(),
        '25_34': users.filter(dob__year__gte=date.today().year - 34, dob__year__lte=date.today().year - 25).count(),
        '35_44': users.filter(dob__year__gte=date.today().year - 44, dob__year__lte=date.today().year - 35).count(),
        '45_54': users.filter(dob__year__gte=date.today().year - 54, dob__year__lte=date.today().year - 45).count(),
        '55_64': users.filter(dob__year__gte=date.today().year - 64, dob__year__lte=date.today().year - 55).count(),
        'over_65': users.filter(dob__lt=date.today().replace(year=date.today().year - 65)).count(),
    }

    # Calculate percentages
    age_distribution = {age_range: (count / total_users) * 100 for age_range, count in age_ranges.items()}

    gender_distribution = {
        'Male': users.filter(gender='M').count(),
        'Female': users.filter(gender='F').count(),
        'Other': users.filter(gender='O').count(),
    }

    # Calculate percentages
    gender_percentages = {gender: (count / total_users) * 100 for gender, count in gender_distribution.items()}
    
     # Aggregate data for each customer
    customer_data = {}
    for order in orders:
        customer_id = order.user.id
        if customer_id not in customer_data:
            customer_data[customer_id] = {
                'customer_name': f"{order.user.user_fname} {order.user.user_lname}",
                'total_orders': 0,
                'total_order_value': 0,
                'most_purchased_shirt': None,
            }
        customer_data[customer_id]['total_orders'] += 1
        customer_data[customer_id]['total_order_value'] += order.total_price

        # Update most purchased shirt
        product = order.orderitem_set.values('product').annotate(count=Count('product')).order_by('-count').first()
        if product:
            product_id = product['product']
            product_name = Product.objects.get(id=product_id).product_name
            customer_data[customer_id]['most_purchased_shirt'] = product_name

    # Calculate average order value for each customer
    for customer_id, data in customer_data.items():
        total_orders = data['total_orders']
        total_order_value = data['total_order_value']
        average_order_value = total_order_value / total_orders if total_orders > 0 else 0

        # Update customer data with calculated metrics
        customer_data[customer_id]['average_order_value'] = average_order_value

    shop = get_shop_info()
    # Prepare data for the PDF template
    context = {
        'shop':shop,
        'date_range': f"{start_date.strftime('%B')} {start_date.year}",
        'age_distribution': age_distribution,
        'gender_percentages': gender_percentages,
        'customer_data': customer_data,
    }

    template = get_template('customer_report.html')
    html = template.render(context)

    # Convert HTML to PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{date_range}_customer_report.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('PDF generation error')

    return response


def generate_report(request, date_range):
    # Define time periods
    time_periods = {
        'today': (timezone.now().date(), timezone.now().date()),
        'last_7_days': (timezone.now().date() - timezone.timedelta(days=7), timezone.now().date()),
        'this_month': (timezone.now().replace(day=1).date(), timezone.now().date()),
        'last_month': ((timezone.now().replace(day=1) - timezone.timedelta(days=1)).replace(day=1).date(), (timezone.now().replace(day=1) - timezone.timedelta(days=1)).date()),
        'this_year': (timezone.now().replace(month=1, day=1).date(), timezone.now().date()),
    }

    # Get start and end dates based on the selected date range
    start_date, end_date = time_periods[date_range]

    # Fetch relevant data from the database
    orders = Order.objects.filter(
        created_at__range=[start_date, end_date]
    ).exclude(order_status='cancelled')
    total_orders = orders.count()
    total_revenue = orders.aggregate(total_revenue=Sum('total_price'))['total_revenue'] if total_orders > 0 else 0
    # print("total orders : ",total_orders)
    # print("total revenue : ",total_revenue)
    # Calculate average order value
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0

    unique_customer_ids = orders.values_list('user_id', flat=True).distinct()

    # Calculate the total number of unique customers
    total_customers = len(unique_customer_ids)
    # Get top-selling products
    top_selling_products = Product.objects.filter(
        orderitem__order__in=orders
    ).annotate(
        total_quantity=Sum('orderitem__quantity')
    ).order_by('-total_quantity')[:3]

    # Get slow-moving products
    # Extract IDs of top-selling products
    top_selling_product_ids = [product.id for product in top_selling_products]

    # Filter slow-moving products based on the extracted IDs
    slow_moving_products = Product.objects.exclude(id__in=top_selling_product_ids) \
    .annotate(total_quantity=Coalesce(Sum('orderitem__quantity'), Value(0))) \
    .order_by('total_quantity')[:3]

    # Calculate revenue by product category
    category_revenue = {}
    categories = Product_category.objects.all()
    
    for category in categories:
    # Filter order items for the current category and time range, excluding cancelled orders
        order_items = OrderItem.objects.filter(
            product__category=category,
            order__created_at__range=[start_date, end_date],
            order__order_status__in=['created', 'in process', 'out for delivery', 'delivered']
        )

        # Calculate total revenue for the category
        ctotal_revenue = 0
        for item in order_items:
            # Determine the price to use based on the discount_price and price fields
            price = item.product.price if item.product.discount_price == 0 else item.product.discount_price
            ctotal_revenue += price * item.quantity

        # Store the total revenue for the category
        category_revenue[category.product_category_name] = ctotal_revenue

    # Calculate the breakdown of sales by payment method
    payment_methods = orders.values('payment_method').annotate(total_orders=Count('id'))
    payment_breakdown = {payment['payment_method']: payment['total_orders'] / total_orders * 100 for payment in payment_methods}

    shop = get_shop_info()
    # Prepare data to pass to the template
    context = {
        'date_range': f"{start_date.strftime('%B')} {start_date.year}",
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'average_order_value': average_order_value,
        'top_selling_products': top_selling_products,
        'slow_moving_products': slow_moving_products,
        'category_revenue': category_revenue,
        'payment_breakdown': payment_breakdown,
        'total_customers':total_customers,
        'shop':shop,
    }

    # Render the sales report HTML template
    template = get_template('sales_report.html')
    html = template.render(context)

    # Convert HTML to PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{date_range}_sales_report.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('PDF generation error')

    return response


def generate_invoice(request):
    order_id = request.GET.get("oid")
    # Fetch order details from the database
    order = Order.objects.get(id=order_id)
    order_items = OrderItem.objects.filter(order=order)

    # Create a buffer for the PDF
    buffer = BytesIO()

    # Create PDF
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    style_heading = styles["Heading1"]
    style_body = styles["BodyText"]
    style_order_items = ParagraphStyle(name="OrderItems", parent=style_heading, fontSize=16, leading=18, leftIndent=0, spaceBefore=20, spaceAfter=20, textColor=colors.black, fontName='Helvetica-Bold')

    # Content for the PDF
    content = []

    # Add heading with centered company name
    company_name = "<u><b>Style-x Shirts</b></u>"  # Updated company name with underline
    heading = Paragraph(f"<para align=center fontSize=20>{company_name}</para>", style_heading)
    content.append(heading)
    content.append(Spacer(1, 12))

    # Add company address centered
    company_address = "raj complax,geekanta,ahmedabad - 382340"  # Example company address
    address_paragraph = Paragraph(f"<para align=center>{company_address}</para>", style_body)
    content.append(address_paragraph)

    # Calculate line width dynamically based on page width
    line_width = pdf.width - inch * 4.6  # Subtracting 1 inch for margin
    line = "-" * int(line_width)  # Creating a line with calculated width
    content.append(Paragraph(line, style_body))
    content.append(Spacer(1, 12))

    # Add Invoice Number and Date
    invoice_details = f"Invoice Number: INV-{order_id}     Date: {order.created_at.strftime('%B %d, %Y')}"
    invoice_details_paragraph = Paragraph(f"<para align=left fontSize=12>{invoice_details}</para>", style_body)
    content.append(invoice_details_paragraph)

    # Add Bill To (User data)
    bill_to = "<b>Bill To:</b><br/>"
    bill_to += f"{order.user.user_fname} {order.user.user_lname}<br/>"
    bill_to += f"{order.user.house_street}<br/>"
    bill_to += f"{order.user.city}, {order.user.state}, {order.user.pincode}<br/>"
    bill_to += f"Email: {order.user.user_email}<br/>"
    bill_to += f"Phone: {order.user.user_contact}<br/>"
    content.append(Paragraph(bill_to, style_body))
    content.append(Spacer(1, 12))

    # Add Deliver (Billing data)
    deliver_to = "<b>Deliver To:</b><br/>"
    deliver_to += f"{order.billing_address.fname} {order.billing_address.lname}<br/>"
    deliver_to += f"{order.billing_address.house_street}<br/>"
    deliver_to += f"{order.billing_address.city}, {order.billing_address.state}, {order.billing_address.pincode}<br/>"
    deliver_to += f"Email: {order.billing_address.email}<br/>"
    deliver_to += f"Contact: {order.billing_address.contact}<br/>"
    content.append(Paragraph(deliver_to, style_body))

    # Add line separator
    content.append(Paragraph(line, style_body))
    content.append(Spacer(1, 12))

    # Add order items
    order_items_content = [["Description", "Quantity", "Price per Unit", "Total Amount"]]
    for order_item in order_items:
        price = order_item.product.discount_price if order_item.product.discount_price != 0 else order_item.product.price
        order_items_content.append([
            order_item.product.product_name,
            str(order_item.quantity),
            "Rs. {:.2f}".format(price),  # Use discounted price if available, else use regular price
            "Rs. {:.2f}".format(order_item.subtotal()),  # Use Rs. symbol and format subtotal
        ])

    # Define column widths for the table
    col_widths = [250, 70, 70, 70]  # Adjust as needed

    order_items_table = Table(order_items_content, colWidths=col_widths)
    order_items_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                           ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                                           ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                                           ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                                           ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                                           ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                           ]))
    content.append(order_items_table)

    # Calculate total
    total_price = sum(order_item.subtotal() for order_item in order_items)

    # Add total
    total = "<b>Total (Inclusive of all taxes) : </b>"
    total += "Rs. {:.2f}".format(total_price)  # Use Rs. symbol and format total
    content.append(Paragraph(total, style_body))

    # Add computer-generated invoice note
    computer_generated_note = "<b>This is a computer-generated invoice.</b>"
    content.append(Paragraph(computer_generated_note, style_body))

    # Build PDF
    pdf.build(content)

    # Get PDF buffer value and return as response
    pdf_buffer = buffer.getvalue()
    buffer.close()
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order_id}.pdf"'
    response.write(pdf_buffer)
    return response


# def generate_invoice(request):
#     order_id = request.GET.get("oid")
#     # Fetch order details from the database
#     order = Order.objects.get(id=order_id)
#     order_items = OrderItem.objects.filter(order=order)

#     # Create a buffer for the PDF
#     buffer = BytesIO()

#     # Create PDF
#     pdf = SimpleDocTemplate(buffer, pagesize=letter)
#     styles = getSampleStyleSheet()
#     style_heading = styles["Heading1"]
#     style_body = styles["BodyText"]
#     style_order_items = ParagraphStyle(name="OrderItems", parent=style_heading, fontSize=16, leading=18, leftIndent=0, spaceBefore=20, spaceAfter=20, textColor=colors.black, fontName='Helvetica-Bold')

#     # Content for the PDF
#     content = []

#     # Add heading with centered company name
#     company_name = "<u><b>Style-x Shirts</b></u>"  # Updated company name with underline
#     heading = Paragraph(f"<para align=center fontSize=20>{company_name}</para>", style_heading)
#     content.append(heading)
#     content.append(Spacer(1, 12)) 

#     # Add Invoice Number and Date
#     invoice_details = f"Invoice Number: INV-{order_id}     Date: {order.created_at.strftime('%B %d, %Y')}"
#     invoice_details_paragraph = Paragraph(f"<para align=left fontSize=12>{invoice_details}</para>", style_body)
#     content.append(invoice_details_paragraph)

#     # Add Bill To (User data)
#     bill_to = "<b>Bill To:</b><br/>"
#     bill_to += f"{order.user.user_fname} {order.user.user_lname}<br/>"
#     bill_to += f"{order.user.house_street}<br/>"
#     bill_to += f"{order.user.city}, {order.user.state}, {order.user.pincode}<br/>"
#     bill_to += f"Email: {order.user.user_email}<br/>"
#     bill_to += f"Phone: {order.user.user_contact}<br/>"
#     content.append(Paragraph(bill_to, style_body))
#     content.append(Spacer(1, 12)) 

#     # Add Deliver (Billing data)
#     deliver_to = "<b>Deliver To:</b><br/>"
#     deliver_to += f"{order.billing_address.fname} {order.billing_address.lname}<br/>"
#     deliver_to += f"{order.billing_address.house_street}<br/>"
#     deliver_to += f"{order.billing_address.city}, {order.billing_address.state}, {order.billing_address.pincode}<br/>"
#     deliver_to += f"Email: {order.billing_address.email}<br/>"
#     deliver_to += f"Contact: {order.billing_address.contact}<br/>"
#     content.append(Paragraph(deliver_to, style_body))

#     # Add line separator
#     content.append(Spacer(1, 12))
   

#     # Add order items
#     order_items_content = [["Description", "Quantity", "Price per Unit", "Total Amount"]]
#     for order_item in order_items:
#         price = order_item.product.discount_price if order_item.product.discount_price != 0 else order_item.product.price
#         order_items_content.append([
#             order_item.product.product_name,
#             str(order_item.quantity),
#             "Rs. {:.2f}".format(price),  # Use discounted price if available, else use regular price
#             "Rs. {:.2f}".format(order_item.subtotal()),  # Use Rs. symbol and format subtotal
#         ])

#     # Define column widths for the table
#     col_widths = [250, 70, 70, 70]  # Adjust as needed

#     order_items_table = Table(order_items_content, colWidths=col_widths)
#     order_items_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'LEFT'),
#                                            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
#                                            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
#                                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
#                                            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
#                                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
#                                            ]))
#     content.append(order_items_table)

#     # Calculate total
#     total_price = sum(order_item.subtotal() for order_item in order_items)

#     # Add total
#     total = "<b>Total (Inclusive of all taxes) : </b>"
#     total += "Rs. {:.2f}".format(total_price)  # Use Rs. symbol and format total
#     content.append(Paragraph(total, style_body))

#     # Add computer-generated invoice note
#     computer_generated_note = "<b>This is a computer-generated invoice.</b>"
#     content.append(Paragraph(computer_generated_note, style_body))

#     # Build PDF
#     pdf.build(content)

#     # Get PDF buffer value and return as response
#     pdf_buffer = buffer.getvalue()
#     buffer.close()
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="invoice_{order_id}.pdf"'
#     response.write(pdf_buffer)
#     return response

def contactMessage(request):
    if request.method == 'POST':
        name = request.POST.get("name","")
        email = request.POST.get("email","")
        msg = request.POST.get("msg","")
        ContactMessage.objects.create(
            name=name,
            email=email,
            message=msg,
        )
        msg = "message send successfully."
        return render(request,"app/contact.html",{"msg":msg})
    else:
        return render(request,"app/contact.html")


def sendOtp(email):
    subject = "OTP Verification!!!"
    otp = randint(100000,999999)
    message = f"OTP-{otp} for style-x shirt website registration."
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject,message,from_email,recipient_list,fail_silently=False)
    return otp

def resendOtp(request,email): 
    otp = sendOtp(email)
    request.session["otp"] = otp
    msg = "otp send successfully."
    if 'fpass' in request.session:
        return redirect(reverse('forgetPasswordOtp') + "?msg=" + msg)
    else:
        return redirect(reverse('otpPage') + "?msg=" + msg)

    

# all pages rendering.
def indexPage(request):
    products = Product.objects.order_by('-created_at')[:8]
    return render(request,"app/index.html",{"products":products})

def shopPage(request):
    selectedsizes = []
    if "size" in request.GET:
        selectedsizes = request.GET.getlist("size")
        try:
            selectedsizes = list(map(int, selectedsizes))
        except ValueError:
            pass
    
    
    all_shirts = Product.objects.prefetch_related('imgs').all()
    query = request.GET.get('q','default')
    filt = request.GET.get('f','default')
    min_price = request.GET.get('min_price','default')
    max_price = request.GET.get('max_price','default')
    collection = request.GET.get('collection','default')
    discount = request.GET.get('discount','default')    

    if selectedsizes:
        # Assuming each product has only one size
        all_shirts = all_shirts.filter(sizes__id__in=selectedsizes)

    if discount!="default" and discount!="":
        try:
            offer = Offer.objects.get(discount_percentage=discount)
            all_shirts =  all_shirts.filter(offer=offer)
        except Offer.DoesNotExist:
            pass
    if collection!="default" and collection!="":
        colid = CollectionTag.objects.get(name=collection)
        all_shirts = all_shirts.filter(collection_tag=colid.id)

    if query!="default" and query!="":

        all_shirts = all_shirts.filter(
            Q(product_name__icontains=query) |
            Q(colors__product_color__icontains=query) |
            Q(product_description__icontains=query) |
            Q(category__product_category_name__icontains=query) |  # Use __product_category_name directly on the ForeignKey field
            Q(sizes__product_size__icontains=query) |
            Q(material__product_material__icontains=query) |  # Use __product_material directly on the ForeignKey field
            Q(price__icontains=query) |
            Q(offer__discount_percentage__icontains=query) 
        ).distinct()
    

    if filt!="default" and filt!="":      
        all_shirts = all_shirts.filter(category__product_category_name=filt)
    
    if min_price != "default" and min_price != "":
        if max_price != "default" and max_price != "":
            all_shirts = all_shirts.filter(
                Q(discount_price__gt=0, discount_price__range=(min_price, max_price)) |
                Q(discount_price=0, price__range=(min_price, max_price))
            )
        else:
            all_shirts = all_shirts.filter(
                Q(discount_price__gt=0, discount_price__gte=min_price) |
                Q(discount_price=0, price__gte=min_price)
            )
    else:
        if max_price != "default" and max_price != "":
            all_shirts = all_shirts.filter(
                Q(discount_price__gt=0, discount_price__lte=max_price) |
                Q(discount_price=0, price__lte=max_price)
            )
            
    
    sort_param = request.GET.get('sort', 'default')
    page_param = request.GET.get('page', 1)
    # Apply sorting based on the selected option
    if sort_param == 'name_az' or sort_param=="default" or sort_param=="":
        all_shirts = all_shirts.order_by('product_name')
    elif sort_param == 'name_za':
        all_shirts = all_shirts.order_by('-product_name')
    elif sort_param == 'price_low_high':
        # all_shirts = all_shirts.order_by('price')
        all_shirts = sorted(all_shirts, key=lambda x: x.discount_price if x.discount_price else x.price)
    elif sort_param == 'price_high_low':
        # all_shirts = all_shirts.order_by('-price')
        all_shirts = sorted(all_shirts, key=lambda x: x.discount_price if x.discount_price else x.price, reverse=True)

    paginator = Paginator(all_shirts,6)
    page_no = request.GET.get('page',page_param)
    shirt_page = paginator.get_page(page_no)
    total_page = shirt_page.paginator.num_pages
    current_page = paginator.page(page_no)

    categories = Product_category.objects.all()
    sizes =  Product_size.objects.all()

    return render(request,"app/shop.html",{
        "all_shirts":shirt_page,
        "total_page":total_page,
        "page_list":[n+1 for n in range(total_page)],
        "current_page":current_page,
        "categories":categories,
        "sizes":sizes,
        "selectedsizes":selectedsizes
        })
    
def aboutPage(request):
    return render(request,"app/about.html")

def contactPage(request):
    return render(request,"app/contact.html")

def cartPage(request):
    if ('email' in request.session) and ('islogin' in request.session) and (request.session["islogin"]==True):
        messages = request.GET.getlist('msg')
        user = User.objects.get(user_email=request.session["email"])
        cart = user.cart
        cart_items = user.cart.cart_item_set.all()
        product_images = []

        for item in cart_items:
            first_image = item.product.imgs.first()
            if first_image:
                product_images.append(first_image.image.url)
            else:
                product_images.append(None)
        items = zip(cart_items,product_images)
        items = list(items)
        # print(items)
        # for i in items:
            # print(i[1])
            # print(i[0].product.product_name)
            # print(i[1])
        # print(list(items)[0][0].quantity)
        # print(cart.cart_item_set.count)
        return render(request,"app/cart.html",{'user':user,'cart':cart,'cart_items':items,'messages':messages})
    else:
        return render(request,"app/cart.html",{'msg':"cart is empty!! please add some items."})

def productDetailsPage(request,pid):
    try:
        product = get_object_or_404(Product, pk=pid)
    except Http404:
        return render(request,"app/shop.html")   
    images = product.imgs.all()
    data = {
        'shirt':product,
        'imgs':images,
    }
    return render(request,"app/product-details.html",data)

def loginPage(request):
    return render(request,"app/login.html")

def forgetpasswordPage(request):
    return render(request,"app/forgetpassword.html")

def otpPage(request):
    return render(request,"app/otp.html")

def resetpasswordPage(request):
    return render(request,"app/resetpassword.html")

def registerPage(request):
    return render(request,"app/register.html")

def userProfilePage(request):
    if ('email' in request.session) and ('islogin' in request.session) and (request.session["islogin"] == True):
        user = User.objects.get(user_email=request.session['email'])
        if user.dob:
            dob = datetime.strftime(user.dob, "%Y-%m-%d")
        else:
            dob = ""
        return render(request,'app/user-profile.html',{"user":user,"dob":dob})
    else:
        return redirect('loginPage')




# ============= manage order ====================

def checkoutPage(request):
    if ('email' in request.session) and ('islogin' in request.session) and (request.session["islogin"] == True):
        if request.GET.get('source') == 'redirect':
            user = User.objects.get(user_email=request.session["email"])
            paymentid =  request.session['paymentid']
            if paymentid:
                client = razorpay.Client(auth=(RAZORPAY_API_KEY,RAZORPAY_SECRET_KEY))
                payment_obj = client.order.fetch(paymentid)
            else:
                payment_obj = None
            if request.GET.get('pid'):
                product = Product.objects.get(pk=request.GET.get('pid'))
                pqty = request.GET.get("pqty",1)
                return render(request,"app/check-out.html",{"user":user,"key":RAZORPAY_API_KEY,"shirt":product,"payment":payment_obj,"pqty":pqty})
            elif request.GET.get('cid'):
                cart = Cart.objects.get(pk=request.GET.get('cid'))
                cartitems = Cart_item.objects.filter(cart=request.GET.get('cid'))
                return render(request,"app/check-out.html",{"user":user,"key":RAZORPAY_API_KEY,"shirts":cartitems,"payment":payment_obj,"totalprice":int(cart.total_price)})
            else:
                return redirect("shopPage")
                
        else:
            return redirect("shopPage")
    else:
        return redirect("loginPage")

from django.urls import reverse
# creating order for razorpay api
def razorpayOrder(request):
    if ('email' in request.session) and ('islogin' in request.session) and (request.session["islogin"] == True):
        client = razorpay.Client(auth=(RAZORPAY_API_KEY,RAZORPAY_SECRET_KEY))
        user = User.objects.get(user_email=request.session['email'])
        from_page = request.GET.get("from_page","default")
        pqty = int(request.GET.get('qty',1))
        if 'productid' in request.session:
            request.session.pop('productid')
        if 'cartid' in request.session:
            request.session.pop('cartid')
        if from_page == "shop" or from_page == "productDetails":
            product = Product.objects.prefetch_related('imgs').get(pk=request.GET.get("pid"))
            request.session["productid"] = request.GET.get("pid")

            if product.stock_quantity < pqty:

                msg = "insufficiant stock quantity"
                request.session['msg'] = msg
                if from_page == 'shop':
                    return redirect('shopPage')
                if from_page == 'productDetails':
                    return redirect("productdetailsPage", pid=product.id)
                return redirect("shopPage")

            DATA = {
                    "currency": "INR",
                    "receipt": "receipt#1",
                    "notes": {
                        "key1": "value3",
                        "key2": "value2"
                            }
                }
            if product.discount_price == 0:
                DATA["amount"] = int(product.price * pqty * 100)
            else:
                DATA["amount"] = int(product.discount_price * pqty * 100)

            payment =client.order.create(data=DATA)
            request.session["paymentid"] =  payment["id"]
            request.session["qty"] =  pqty
            # return redirect("checkoutPage?source=redirect&pid=" + request.GET.get("pid")) 
            return redirect(reverse("checkoutPage") + "?source=redirect&pid=" + request.GET.get("pid") + "&pqty=" + str(pqty))
        elif from_page == "cart" :
            cart = Cart.objects.get(pk=request.GET.get('cid'))
            request.session["cartid"] = request.GET.get('cid')
            DATA = {
                    "amount":int(cart.total_price * 100),
                    "currency": "INR",
                    "receipt": "receipt#1",
                    "notes": {
                        "key1": "value3",
                        "key2": "value2"
                            }
                }
            payment =  client.order.create(data=DATA)
            request.session["paymentid"] = payment["id"]
            # return redirect( "checkoutPage?source=redirect&pid=" + request.GET.get("cid")) 
            return redirect(reverse("checkoutPage") + "?source=redirect&cid=" + request.GET.get("cid"))
        else:
            return redirect("shopPage")
    else:
        return redirect("loginPage")


def orderDetailsPage(request):
    if ('email' in request.session) and ('islogin' in request.session) and (request.session["islogin"] == True):
        if 'orderid' in request.GET:
            order = Order.objects.get(pk=request.GET['orderid'])
            orderitems = OrderItem.objects.filter(order=request.GET["orderid"])
            return render(request,"app/order-details.html",{"order":order,"orderitems":orderitems})
        else:
            return redirect("shopPage")
    else:
        return redirect("loginPage")
    return render(request,"app/order-details.html")

# payment
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def payment(request):
    if request.method == 'POST':
        # print("this is fucking statring of the session\n\n\n",request.session.items())
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        client = razorpay.Client(auth=(RAZORPAY_API_KEY,RAZORPAY_SECRET_KEY))
        user = User.objects.get(user_email=request.session["email"])
    
        a = client.utility.verify_payment_signature({
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
        })
        if a == True:
            # for every order create new billing address.
            billing_address = BillingAddress.objects.create(
                fname = request.GET.get('fname'),
                lname = request.GET.get('lname'),
                email = request.GET.get('email'),
                contact = request.GET.get('contact'),
                house_street=request.GET.get('house_street'),
                apartment_area=request.GET.get('apartment'),
                city=request.GET.get('city'),
                state=request.GET.get('state'),
                pincode=request.GET.get('pincode'),
                note = request.GET.get('note')
            )
            
            payment_details = client.payment.fetch(razorpay_payment_id)

            oid = Order.objects.create(
                user=user,
                total_price = (payment_details["amount"]/100),
                payment_method = payment_details["method"],
                order_status = 'created',
                billing_address = billing_address,
                razorpay_order_id = razorpay_order_id,
                razorpay_payment_id = razorpay_payment_id,
                is_cancelled = False,
                is_refunded = False
            )

            if 'productid' in request.session and 'cartid' not in request.session:
                # print("\n\nin the fucking product\n\n")
                product = Product.objects.get(pk=request.session.pop('productid'))
                if 'qty' in request.session:
                    pqty = request.session.pop("qty")
                    product.stock_quantity -= pqty
                    OrderItem.objects.create(
                        order=oid,
                        product = product,
                        quantity = pqty
                    )
                    product.save()

            elif 'cartid' in request.session and 'productid' not in request.session:
                # print("\n\nin the fucking cart\n\n")
                cart = Cart.objects.get(pk=request.session.pop("cartid"))
                # print("in cart",cart)
                cartitems = Cart_item.objects.filter(cart=cart)
                for item in cartitems:
                    OrderItem.objects.create(
                        order=oid,
                        product = item.product,
                        quantity = item.quantity
                    )
                    item.delete()
                cart.total_price = 0
                cart.save()
            if 'productid' in request.session:
                request.session.pop('productid')
            if 'cartid' in request.session:
                request.session.pop('cartid')

            order_items = OrderItem.objects.filter(order=oid)

            # Prepare order details for the email
            order_details = {
                'order': oid,
                'order_items': order_items,
                'user':user,  # Include all order items
                # Add more order details as needed...
            }

            # Render email template with order details
            email_html_message = render_to_string('email/order_confirmation.html', {'order_details': order_details})
            email_plain_message = strip_tags(email_html_message)

            # Send the email
            send_mail(
                'Order Confirmation',  # Email subject
                email_plain_message,  # Plain text email content
                'your_email@example.com',  # Sender email
                [user.user_email],  # Recipient email(s)
                html_message=email_html_message,  # HTML email content
            )


            # print("this is fucking ending of the session\n\n\n",request.session.items())
            return redirect(reverse("orderDetailsPage") + "?orderid=" + str(oid.id) )
        else:
            return HttpResponse("Payment fail !!!")
    return redirect('shopPage')

def cancelOrder(request):
    if ('email' in request.session) and ('islogin' in request.session) and (request.session["islogin"] == True):
        if 'oid' in request.GET and request.GET["oid"]:
            user = User.objects.get(user_email=request.session["email"])
            order = Order.objects.get(pk=request.GET["oid"])
            orderitems = OrderItem.objects.filter(order=order)
            for item in orderitems:
                product = Product.objects.get(pk=item.product.id)
                product.stock_quantity += item.quantity
                product.save()
            order.is_cancelled = True
            order.order_status = "cancelled"
            order.save()

            order_details = {
                'order': order,
                'order_items': orderitems,
                'user':user,  # Include all order items
                # Add more order details as needed...
            }

            # Render email template with order details
            email_html_message = render_to_string('email/order-cancel.html', {'order_details': order_details})
            email_plain_message = strip_tags(email_html_message)

            # Send the email
            send_mail(
                'Order Cancellation',  # Email subject
                email_plain_message,  # Plain text email content
                'your_email@example.com',  # Sender email
                [user.user_email],  # Recipient email(s)
                html_message=email_html_message,  # HTML email content
            )

            msg = "order cancelled successfully."
            request.session['msg'] = msg
            return redirect("activeOrderPage")
        else:
            return redirect("activeOrderPage")

    else:
        return redirect("loginPage")

def activeOrderPage(request):
    if ('email' in request.session) and ('islogin' in request.session) and (request.session["islogin"] == True):
        user = User.objects.get(user_email=request.session['email'])
        orders = Order.objects.filter(user=user,is_cancelled=False).exclude(order_status='delivered').order_by('-created_at')
        cancelorder = Order.objects.filter(user=user,is_cancelled=True,is_refunded=False).order_by('-created_at')
        return render(request,"app/active-order.html",{"orders":orders,"cancels":cancelorder})
    else:
        return redirect("loginPage")

def activeOrderDetailsPage(request):
    if 'oid' in request.GET and request.GET['oid']:
        order = Order.objects.get(pk=request.GET['oid'])
        orderitems = order.orderitem_set.all()
        return render(request,"app/active-order-details.html",{"order":order,"orderitems":orderitems}) 
    else:
        return redirect("activeOrderPage")

def orderHistoryPage(request):
    user = User.objects.get(user_email=request.session['email'])
    orders = Order.objects.filter(
    Q(user=user) & (Q(order_status='delivered') | (Q(is_cancelled=True) & Q(is_refunded=True)))
    )

    return render(request,"app/order-history.html",{"orders":orders})
# ==========================================================

# registration and log in and manage profile

def registration(request):
    if request.method == "POST":
        if 'registerbtn' in request.POST:
            
            request.session['fname'] = request.POST['fname']
            request.session['lname'] = request.POST['lname']
            email = request.session['email'] = request.POST['email']
            password = request.session['password'] = request.POST['password']
            cpassword = request.POST['cpassword']

            user = User.objects.filter(user_email=email)
            if user:
                msg = "User Already Exists."
                return render(request,"app/register.html",{"msg":msg})
            if password==cpassword:
                otp = sendOtp(email)
                request.session["otp"] = otp
                return render(request,"app/otp.html")
            else:
                msg = "Password and confirm password doesn't match!!"
                return render(request,"app/register.html",{"msg":msg})
        if 'otpbtn' in request.POST:
            uotp = int(request.POST["otp"])
            role = Role.objects.get(role_name="user")
            if int(request.session["otp"]) == uotp:
                newuser = User.objects.create(user_fname=request.session["fname"],user_lname=request.session['lname'],user_email=request.session['email'],user_password=make_password(request.session['password']),role_id=role)
                register = "Account Created Successfully."
                Cart.objects.create(user=newuser)
                request.session.flush()
                return render(request,"app/login.html",{"register":register})
            else:
                msg = "wrong otp!!!"
                return render(request,"app/otp.html",{"msg":msg})

    return render(request,"app/register.html")

def login(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        try:
            user = User.objects.get(user_email=email)
        except User.DoesNotExist:
            fail = "User not found!!!"
            return render(request, "app/login.html", {"fail": fail})
        if check_password(password,user.user_password):
            request.session['fname'] = user.user_fname
            request.session['lname'] = user.user_lname
            request.session['email'] = user.user_email
            request.session['mobile'] = user.user_contact
            request.session['islogin'] = True
            return redirect("indexPage")
        else:
            fail = "Wrong password!!!"
            return render(request,"app/login.html",{"fail":fail})

    return redirect("indexPage")

def logout(request):
    request.session.flush()
    return redirect('indexPage')

def updateProfile(request):
    user = User.objects.get(user_email=request.session['email'])
    fname = request.POST.get('fname')
    lname = request.POST.get('lname')
    dob = request.POST.get('date')
    gender = request.POST.get('gender')
    mobile = request.POST.get('mobile')
    email = request.POST.get('email')
    house = request.POST.get('house')
    apartment = request.POST.get('apartment')
    city = request.POST.get('city')
    state = request.POST.get('state')
    pincode = request.POST.get('pincode')

    user.user_fname = fname
    user.user_lname = lname
    if dob:
        dob = datetime.strptime(dob, '%Y-%m-%d').date()
    else:
        dob = None

    # Validate dob
    if dob and (dob >= now().date() or dob.year <= 1900):
        request.session["msg"] = "Please select valid date of birth."
        return redirect('userProfilePage')
    if dob != "":
        user.dob = dob
    user.user_email = email
    user.gender = gender
    user.user_contact = mobile
    user.house_street = house
    user.apartment_area = apartment
    user.city = city
    user.state = state
    user.pincode = pincode
    user.save()
    request.session["msg"] = "Profile updated successfully."
    return redirect('userProfilePage')

# forgot password 
def forgetPasswordOtpPage(request):
    return render(request,"app/forgetpasswordotp.html")


def forgotPassword(request):
    if request.method=="POST":
        try:
            user = User.objects.get(user_email = request.POST["email"])
        except User.DoesNotExist:
            msg = "User not found!!!"
            return render(request,"app/forgetpassword.html",{"fail":msg})
        request.session["email"] = request.POST["email"]
        request.session["otp"] = sendOtp(request.session["email"])
        request.session["fpass"] = True
        return redirect("forgetPasswordOtp")
    else:
        return redirect("forgetpasswordPage")

def resetPassword(request):
    if request.method=="POST":
        uotp = int(request.POST['otp'])
        if int(request.session["otp"]) == uotp:
            return render(request,"app/resetpassword.html")
        else:
            msg = "Wrong OTP!!!"
            return render(request,"app/forgetpasswordotp.html",{"msg":msg})
    else:
        return render(request,"app/login.html")

def setResetPassword(request):
    if request.method=="POST":
        password = request.POST["pass"]
        cpassword = request.POST["cpass"]
        if password == cpassword:
            user = User.objects.get(user_email=request.session["email"])
            user.user_password = make_password(password)
            user.save()
            msg = "Password updated successfully."
            return render(request,"app/login.html",{"msg":msg})
        else:
            msg = "Password confirm password doesn't match!!!"
            return render(request,"app/resetpassword.html",{"fail":msg})
    else:
        return render(request,"app/login.html")

# add to cart

def addToCart(request, pid):
    if ('email' in request.session) and ('islogin' in request.session) and (request.session["islogin"] == True):
        shirt = Product.objects.get(id=pid)
        user = User.objects.get(user_email=request.session["email"])
        cart = Cart.objects.get(user=user)
        from_page = request.GET.get('from_page','default')
        pqty = request.GET.get('qty',1)
        # Determine the source of the request (shop page or product details page)
        if from_page == 'shopPage':
            qty = 1  # Quantity to add from the shop page
        elif from_page == 'productdetailsPage':
            qty = pqty  # Quantity to add from the product details page
        else:
            qty = 1  # Default quantity

        qty = int(qty)
        # Check if the requested quantity is available in stock
        if shirt.stock_quantity >= qty:
            # Check if the product is already in the cart
            cart_item, created = Cart_item.objects.get_or_create(cart=cart, product=shirt)

            # If the product is not in the cart, create a new cart item
            if created:
                cart_item.quantity = qty
            else:
                # If the product is already in the cart, update the quantity
                cart_item.quantity += qty
                if from_page == 'productdetailsPage' and int(cart_item.quantity) > 10:
                    message = "Cannot add more than 10 quantities for this product."
                    request.session["msg"] = message
                    return redirect("productdetailsPage", pid=shirt.id)
                if from_page == 'shopPage' and int(cart_item.quantity) > 10:
                    message = "Cannot add more than 10 quantities for this product."
                    request.session["msg"] = message
                    return redirect("shopPage")

            shirt.stock_quantity -= qty
            shirt.save()
            cart_item.save()

            if shirt.discount_price == 0:
                cart.total_price += qty * shirt.price
            else:
                cart.total_price += qty * shirt.discount_price

            #2700 = 2700 + 1200 3900
            cart.save()

            return redirect("cartPage")
        else:
            msg = "insufficiant quantity"
            request.session['msg'] = msg
            if from_page == 'shopPage':
                return redirect('shopPage')
            if from_page == 'productdetailsPage':
                return redirect("productdetailsPage", pid=shirt.id)
            return redirect("productdetailsPage", pid=shirt.id)
            
    else:
        # Redirect to login page if user is not authenticated
        return render(request, "app/login.html")


def removeFromCart(request, cid):
    # Retrieve the cart item
    cart_item = get_object_or_404(Cart_item, id=cid)

    # Retrieve the associated product
    product = cart_item.product

    # Restore stock
    product.stock_quantity += cart_item.quantity
    product.save()

    cart = cart_item.cart
    cart.total_price -= cart_item.subtotal()
    cart.save()
    # Remove the cart item
    cart_item.delete()

    # Redirect back to the cart page
    return redirect('cartPage')


def updateCart(request):
    if request.method == "POST":
        user = User.objects.get(user_email=request.session['email']) 
        cart = Cart.objects.get(user=user)
        messages = []
        
        # Loop through each item in the cart
        for item in cart.cart_item_set.all():
            
            quantity_key = f'cartQty{item.id}'
            new_quantity = int(request.POST.get(quantity_key, 0))
            additional_qty = abs(new_quantity - item.quantity)
            
            if new_quantity > item.quantity:
                if additional_qty > item.product.stock_quantity:
                    messages.append(f"Sorry, there is insufficient stock for {item.product.product_name}.")
                    continue
                else:
                    if 0 < new_quantity <= 10:
                        item.product.stock_quantity -= additional_qty
                    else:
                        messages.append(f"Sorry, Cannot add more than 10 quantities for {item.product.product_name}.")

            elif new_quantity < item.quantity:    
                item.product.stock_quantity += additional_qty
                        
            item.product.save()
            item.quantity = new_quantity
            item.save()
                

        # Recalculate the total price of the cart
        cart.total_price = sum(item.subtotal() for item in cart.cart_item_set.all())
        cart.save()

        # Redirect back to the cart page
        error_messages = '&'.join([f'msg={msg}' for msg in messages])
        return redirect('/cart' + '?' + error_messages)
