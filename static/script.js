function showLoginForm() {
    document.getElementById("loginForm").style.display = "block";
    document.getElementById("signupForm").style.display = "none";
}

function showSignupForm() {
    document.getElementById("signupForm").style.display = "block";
    document.getElementById("loginForm").style.display = "none";
}

function goToAdminPage() {
    window.location.href = "admin_login.html"; // Assuming admin page is admin.html
}

function login() {
    // Here you would handle the login logic
    // For simplicity, let's assume successful login redirects to chatroom
    window.location.href = "chatroom.html"; // Redirect to chatroom after login
}

function signup() {
    // Here you would handle the signup logic
    // For simplicity, let's assume successful signup redirects to chatroom
    window.location.href = "chatroom.html"; // Redirect to chatroom after signup
}
