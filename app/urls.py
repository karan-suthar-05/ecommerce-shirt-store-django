from django.urls import path,include
from . import views





urlpatterns = [
    # pages urls
    path("",views.indexPage,name="indexPage"),
    path("shop/",views.shopPage,name="shopPage"),
    path("about/",views.aboutPage,name="aboutPage"),
    path("contact/",views.contactPage,name="contactPage"),
    path("cart/",views.cartPage,name="cartPage"),
    path("login/",views.loginPage,name="loginPage"),
    path("register/",views.registerPage,name="registerPage"),
    path("otp/",views.otpPage,name="otpPage"),
    path("forgetpassword/",views.forgetpasswordPage,name="forgetpasswordPage"),
    path("resetpassword/",views.resetpasswordPage,name="resetpasswordPage"),
    path("productdetails/<int:pid>",views.productDetailsPage , name="productdetailsPage"),
    path("userProfilePage/",views.userProfilePage , name="userProfilePage"),
    path("contactMessge/",views.contactMessage , name="contactMessge"),
    
    # manage orders
 
    path("checkoutPage/", views.checkoutPage, name="checkoutPage"),
    path("payment/", views.payment, name="payment"),
    path("razorpayOrder/", views.razorpayOrder, name="razorpayOrder"),
    path("orderDetailsPage/", views.orderDetailsPage, name="orderDetailsPage"),
    path("activeOrderPage/", views.activeOrderPage, name="activeOrderPage"),
    path("activeOrderDetailsPage/", views.activeOrderDetailsPage, name="activeOrderDetailsPage"),
    path("cancelOrder/", views.cancelOrder, name="cancelOrder"),
    path("orderHistoryPage/", views.orderHistoryPage, name="orderHistoryPage"),
    path("generateInvoice/", views.generate_invoice, name="generateInvoice"),


    


    # login and registration and update profile
    path("registration/", views.registration ,name="registration"),
    path("resendOtp/<email>",views.resendOtp,name="resendOtp"),
    path("loginprocess/",views.login,name="loginprocess"),
    path("logout/",views.logout,name="logout"),
    path("updateProfile/",views.updateProfile,name="updateProfile"),
    path("forgetPasswordOtp/",views.forgetPasswordOtpPage,name="forgetPasswordOtp"),

    # forgot password
    path("fpassword/",views.forgotPassword,name="fpassword"),
    path("rpasswrod/",views.resetPassword,name="rpassword"),
    path("srpassword/",views.setResetPassword,name="srpasswrod"),

    # add to cart
    path("addtocart/<int:pid>",views.addToCart,name="addtocart"),
    path("removefromcart/<int:cid>",views.removeFromCart,name="removefromcart"),
    path("updatecart/",views.updateCart,name="updatecart"),

    # generate reports
    


]