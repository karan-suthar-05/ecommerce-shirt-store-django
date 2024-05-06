// menu for phone

var open = document.querySelector(".open");
var close = document.querySelector(".close");
var links = document.getElementById("links");

open.addEventListener('click',()=>{
    links.style.left = "0";
    open.style.display = "none";
    close.style.display = "block";
});
close.addEventListener('click',()=>{
    links.style.left = "-100vw";
    open.style.display = "block";
    close.style.display = "none";
});
// validate password
console.log("fuk ya");

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("registrationForm").addEventListener("submit", function (event) {
        return validatePassword(event);
    });

    function validatePassword(event) {
        var password = document.getElementById('password').value;

        if (password.length < 6) {
            alert('Password must be at least 6 characters long.');
            event.preventDefault(); // Prevent the default form submission
            return false;
        }

        // Additional validation logic or form submission can be added here if needed

        return true;
    }
});