from django.db import models
from django.core.validators import MaxValueValidator
from django.forms import inlineformset_factory
from ckeditor.fields import RichTextField


# Create your models here.
class State(models.Model):
    state_name = models.CharField(max_length=15,null=False, unique=True)
    def __str__(self):
        return self.state_name

class City(models.Model):
    city_name =  models.CharField(max_length=15,null=False, unique=True)
    state_id = models.ForeignKey(State, on_delete=models.CASCADE)
    def __str__(self):
        return self.city_name

class Area(models.Model):
    area_name = models.CharField(max_length=100,null=False, unique=True)
    city_id = models.ForeignKey(City, on_delete=models.CASCADE)   
    def __str__(self):
        return self.area_name

class Company(models.Model):
    company_name = models.CharField(max_length=20,null=False, unique=True)
    company_contact = models.CharField(max_length=10,null=False)
    company_email = models.EmailField(null=False)
    company_address = models.TextField(null=False)
    area_id = models.ForeignKey(Area, on_delete=models.CASCADE)
    def __str__(self):
        return self.company_name

class Role(models.Model):
    role_name = models.CharField(max_length=20,null=False, unique=True)
    company_id = models.ForeignKey(Company, on_delete=models.CASCADE)
    def __str__(self):
        return self.role_name

class User(models.Model):
    user_fname = models.CharField(max_length=20,null=False)
    user_lname = models.CharField(max_length=20,null=False)
    dob = models.DateField(null=True)
    gender = models.CharField(max_length=1,null=True)
    user_contact = models.CharField(max_length=10,null=True)
    house_street = models.CharField(max_length=100, null=True)
    apartment_area = models.CharField(max_length=100, null=True)
    city = models.CharField(max_length=50, null=True)
    state = models.CharField(max_length=50, null=True)
    pincode = models.CharField(max_length=10, null=True)
    user_email = models.EmailField(null=False)
    user_password = models.CharField(max_length=200,null=False)
    role_id =  models.ForeignKey(Role, on_delete=models.CASCADE)
    def __str__(self):
        return self.user_email

class ContactMessage(models.Model):
    name = models.CharField(max_length=100,blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    admin_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Message from {self.name} ({self.email}) - {self.created_at}'

class Product_category(models.Model):
    product_category_name = models.CharField(max_length=50,null=False, unique=True)
    def __str__(self):
        return self.product_category_name

class Product_size(models.Model):
    product_size = models.CharField(max_length=10, unique=True)
    def __str__(self):
        return self.product_size

class Product_color(models.Model):
    product_color = models.CharField(max_length=10, unique=True)
    def __str__(self):
        return self.product_color

class Product_material(models.Model):
    product_material = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.product_material

class Product_image(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE,related_name='imgs')
    image = models.ImageField(upload_to='shirt_images/')

    def __str__(self):
        return f"Image for {self.product.product_name}"

class Offer(models.Model):
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.discount_percentage}% off ({self.start_date} - {self.end_date})"

class CollectionTag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    product_name = models.CharField(max_length=255)
    product_description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Product_category, on_delete=models.CASCADE, null=False)
    product_detail = RichTextField()
    sizes =  models.ForeignKey(Product_size, on_delete=models.CASCADE, null=True)
    colors = models.ForeignKey(Product_color, on_delete=models.CASCADE, null=True)
    material = models.ForeignKey(Product_material, on_delete=models.CASCADE, null=False)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, null=True, blank=True)
    stock_quantity = models.IntegerField(default=0)
    collection_tag = models.ForeignKey(CollectionTag,on_delete=models.CASCADE,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.product_name} ({self.sizes},{self.price if self.discount_price == 0 else self.discount_price})"

class Production(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    production_date = models.DateField()
    production_cost = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity} units produced on {self.production_date}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Update the stock_quantity in the associated product model
        self.product.stock_quantity += self.quantity
        self.product.save()


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Cart for {self.user.user_email}"

class Cart_item(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MaxValueValidator(10)])
    created_at = models.DateTimeField(auto_now_add=True)

    def subtotal(self):
        if self.product.discount_price == 0:
            return self.product.price * self.quantity
        else:
            return self.product.discount_price * self.quantity


    def __str__(self):
        return f"{self.quantity} x {self.product.product_name} in {self.cart} at {self.created_at}"


ShirtImageFormSet = inlineformset_factory(Product, Product_image, fields=('image',), extra=1, can_delete=False)

class BillingAddress(models.Model):
    fname = models.CharField(max_length=100, blank=True, null=True)
    lname = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    contact = models.CharField(max_length=10, blank=True, null=True)
    house_street = models.CharField(max_length=100, blank=True, null=True)
    apartment_area = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        address_lines = [
            f"Name: {self.fname} {self.lname}",
            f"Email: {self.email}",
            f"Contact: {self.contact}",
            f"Address: {self.house_street}, {self.apartment_area}",
            f"City: {self.city}",
            f"State: {self.state}",
            f"Pincode: {self.pincode}",
            f"Note: {self.note}",
        ]
        return '\n'.join(address_lines)

class Order(models.Model):
    PAYMENT_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI'),
        ('wallet','Wallet')
    ]
    ORDER_STATUS = [
        ('created','Created'),
        ('in process','In Process'),
        ('out for delivery','Out For Delivery'),
        ('delivered','Delivered'),
        ('cancelled','Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    billing_address = models.ForeignKey(BillingAddress, on_delete=models.SET_NULL, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    order_status = models.CharField(max_length=50, choices=ORDER_STATUS,blank=True, null=True)
    is_cancelled = models.BooleanField(default=False)  # Field to track if the order is canceled
    is_refunded = models.BooleanField(default=False)   # Field to track if the order is refunded
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.pk)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def subtotal(self):
        if self.product.discount_price == 0:
            return self.product.price * self.quantity
        else:
            return self.product.discount_price * self.quantity

