function navigateTo(role) {
    // This function is called from index.html and correctly navigates 
    // to the role-specific folder.
    window.location.href = `${role}/login.html`;
}

// Unified Login/Signup Functions for index.html
let selectedRole = '';

function toggleToSignup() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('signup-form').style.display = 'block';
}

function toggleToLogin() {
    document.getElementById('signup-form').style.display = 'none';
    document.getElementById('login-form').style.display = 'block';
}

function toggleRoleDropdown() {
    const dropdown = document.getElementById('role-dropdown-menu');
    dropdown.classList.toggle('show');
}

function selectRole(role) {
    selectedRole = role;
    const roleText = role.charAt(0).toUpperCase() + role.slice(1);
    document.getElementById('selected-role-text').textContent = roleText;
    document.getElementById('signup-role-value').value = role;
    document.getElementById('role-dropdown-menu').classList.remove('show');
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const dropdown = document.querySelector('.role-dropdown');
    if (dropdown && !dropdown.contains(event.target)) {
        document.getElementById('role-dropdown-menu').classList.remove('show');
    }
});

// Fancy notification popup functions
let notificationTimeout = null;

function showNotification(title, message, type = 'success') {
    const popup = document.getElementById('notification-popup');
    const icon = document.getElementById('notification-icon');
    const titleEl = document.getElementById('notification-title');
    const messageEl = document.getElementById('notification-message');
    
    // Clear any existing timeout
    if (notificationTimeout) {
        clearTimeout(notificationTimeout);
    }
    
    // Set content
    titleEl.textContent = title;
    messageEl.textContent = message;
    
    // Set icon and style based on type
    if (type === 'success') {
        icon.textContent = '✓';
        popup.className = 'notification-popup success';
    } else if (type === 'error') {
        icon.textContent = '✕';
        popup.className = 'notification-popup error';
    }
    
    // Show popup
    setTimeout(() => {
        popup.classList.add('show');
    }, 10);
    
    // Auto hide after 4 seconds
    notificationTimeout = setTimeout(() => {
        hideNotification();
    }, 4000);
    
    // Pause auto-close on hover
    popup.onmouseenter = () => {
        if (notificationTimeout) {
            clearTimeout(notificationTimeout);
            notificationTimeout = null;
        }
    };
    
    // Close on mouse leave
    popup.onmouseleave = () => {
        hideNotification();
    };
}

function hideNotification() {
    const popup = document.getElementById('notification-popup');
    popup.classList.remove('show');
    
    // Clear timeout if manually closed
    if (notificationTimeout) {
        clearTimeout(notificationTimeout);
        notificationTimeout = null;
    }
    
    // Remove hover listeners
    popup.onmouseenter = null;
    popup.onmouseleave = null;
}

async function handleUnifiedLogin() {
    event.preventDefault();

    const usernameOrEmail = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;

    const data = {
        username: usernameOrEmail,
        password: password
    };

    try {
        const response = await fetch("http://127.0.0.1:5000/unified-login", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        });

        const result = await response.json();
        
        if (result.success) {
            // Store user information in session storage
            sessionStorage.setItem('loggedInUserFirstName', result.firstname);
            sessionStorage.setItem('loggedInUserLastName', result.lastname);
            sessionStorage.setItem('loggedInUserUsername', result.username);
            sessionStorage.setItem('loggedInUserEmail', result.email);
            sessionStorage.setItem('loggedInUserPhone', result.contact);
            sessionStorage.setItem('loggedInUserRole', result.role);
            
            // Wait a brief moment for login to complete, then show success notification
            setTimeout(() => {
                showNotification('Login Successful! 🎉', `Welcome back, ${result.firstname} ${result.lastname}! Redirecting to your dashboard...`, 'success');
            }, 300);
            
            // Redirect after showing the notification
            setTimeout(() => {
                window.location.href = `${result.role}_dashboard.html`;
            }, 1000);
        } else {
            showNotification('Login Failed', result.message || 'Please check your credentials and try again.', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Connection Error', 'Unable to connect to server. Please check your connection and try again.', 'error');
    }

    return false;
}

async function handleUnifiedSignup() {
    event.preventDefault();

    const role = document.getElementById('signup-role-value').value;
    
    if (!role) {
        alert('Please select a role');
        return false;
    }

    const data = {
        username: document.getElementById('signup-new-username').value.trim(),
        password: document.getElementById('signup-new-password').value,
        email: document.getElementById('signup-email').value.trim(),
        firstname: document.getElementById('signup-firstname').value.trim(),
        lastname: document.getElementById('signup-lastname').value.trim(),
        contact: document.getElementById('signup-contact').value.trim(),
        role: role
    };

    try {
        const response = await fetch("http://127.0.0.1:5000/signup", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        });

        const result = await response.json();
        
        if (result.success) {
            showNotification('Account Created! 🎊', 'Your account has been created successfully. Please login to continue.', 'success');
            
            // Clear signup form and switch to login after a short delay
            setTimeout(() => {
                document.getElementById('signup-form').reset();
                selectedRole = '';
                document.getElementById('selected-role-text').textContent = 'Select your role';
                toggleToLogin();
            }, 1500);
        } else {
            showNotification('Signup Failed', result.message || 'Unable to create account. Please try again.', 'error');
        }
    } catch (error) {
        console.error('Signup error:', error);
        showNotification('Connection Error', 'Unable to connect to server. Please check your connection and try again.', 'error');
    }

    return false;
}

/**
 * Determines the role based on the current URL path.
 */
function getCurrentRole() {
    const path = window.location.pathname.toLowerCase();
    if (path.includes('/customer/')) return 'customer';
    if (path.includes('/builder/')) return 'builder';
    if (path.includes('/consultant/')) return 'consultant';
    // Fallback in case of unexpected file path
    return 'customer'; 
}

/**
 * Initializes the login page by setting the title, form headers, 
 * and form submission handlers based on the detected role.
 */
function initializeLoginPage() {
    // Get the current role dynamically
    const role = getCurrentRole();
    
    // Capitalize the first letter for display (e.g., 'customer' -> 'Customer')
    const roleDisplay = role.charAt(0).toUpperCase() + role.slice(1);
    
    // 1. Update the document title
    document.title = `${roleDisplay} Login | Your True RealEstate Partner`;
    
    // 2. Update the form title
    const formTitle = document.getElementById("form-title");
    if(formTitle) formTitle.textContent = `${roleDisplay} Login`;
    
    // 3. Update form submissions and toggle link with the detected role
    const loginForm = document.getElementById("login-form");
    const signupForm = document.getElementById("signup-form");
    const toggleLinkContainer = document.getElementById("toggle-form");

    if (loginForm) loginForm.setAttribute('onsubmit', `return handleLogin('${role}')`);
    if (signupForm) signupForm.setAttribute('onsubmit', `return handleSignup('${role}')`);
    
    // Set the initial toggle state
    if (toggleLinkContainer) {
        toggleLinkContainer.innerHTML = `Don't have an account? <a href="#" onclick="toggleSignup('${role}')">Sign up</a>`;
    }
}

// Toggle login/signup form
function toggleSignup(role) {
    const loginForm = document.getElementById("login-form");
    const signupForm = document.getElementById("signup-form");
    const toggleText = document.getElementById("toggle-form");
    const title = document.getElementById("form-title");
    
    // Capitalize the first letter for display
    const roleDisplay = role.charAt(0).toUpperCase() + role.slice(1);

    if (signupForm.style.display === "none" || signupForm.style.display === "") {
        loginForm.style.display = "none";
        signupForm.style.display = "block";
        title.textContent = `${roleDisplay} Signup`; // Dynamic title
        // Ensure the onclick function is re-added after innerHTML update
        toggleText.innerHTML = `Already have an account? <a href="#" onclick="toggleSignup('${role}')">Login</a>`; 
    } else {
        signupForm.style.display = "none";
        loginForm.style.display = "block";
        title.textContent = `${roleDisplay} Login`; // Dynamic title
        // Ensure the onclick function is re-added after innerHTML update
        toggleText.innerHTML = `Don't have an account? <a href="#" onclick="toggleSignup('${role}')">Sign up</a>`;
    }
}

async function handleSignup(role) {
    event.preventDefault();

    const data = {
        username: document.getElementById(`signup-new-username`).value,
        password: document.getElementById(`signup-new-password`).value,
        email: document.getElementById(`signup-email`).value,
        firstname: document.getElementById(`signup-firstname`).value,
        lastname: document.getElementById(`signup-lastname`).value,
        contact: document.getElementById(`signup-contact`).value,
        role: role // Pass the role to the backend
    };

    const response = await fetch("http://127.0.0.1:5000/signup", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    });

    const result = await response.json();
    alert(result.message);

    if (result.success) {
        // Clear sign-up form and switch to login form
        document.getElementById("signup-form").reset();
        toggleSignup(role);
    }
    return false; // Prevent form submission
}

async function handleLogin(role) {
    event.preventDefault();

    const data = {
        username: document.getElementById(`login-username`).value,
        password: document.getElementById(`login-password`).value,
        role: role // Pass the role to the backend
    };

    const response = await fetch("http://127.0.0.1:5000/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    });

    const result = await response.json();
    alert(result.message);

    if (result.success) {
        // --- CRITICAL UPDATE: Store username and name ---
        sessionStorage.setItem('loggedInUserFirstName', result.firstname);
        sessionStorage.setItem('loggedInUserLastName', result.lastname);
        sessionStorage.setItem('loggedInUserUsername', data.username); // <-- Required for builder_listings.html
        sessionStorage.setItem('loggedInUserEmail', result.email);
        sessionStorage.setItem('loggedInUserPhone', result.contact);
        sessionStorage.setItem('loggedInUserRole', role); // <-- Store the role
        // ------------------------------------------------
        
        // Redirect to a role-specific page (e.g., 'customer_dashboard.html')
        window.location.href = `../${role}_dashboard.html`; 
    }
    return false; // Prevent form submission
}

// Run the initialization logic when the page loads
if (window.location.pathname.includes('login.html')) {
    document.addEventListener('DOMContentLoaded', initializeLoginPage);
}