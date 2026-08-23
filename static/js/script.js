// Navigation Toggle
document.addEventListener('DOMContentLoaded', function() {
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (navToggle) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
    }
    
    // Close menu when clicking a link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            navMenu.classList.remove('active');
        });
    });
    
    // Add to Cart functionality
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.dataset.productId;
            let quantity = 1;
            
            // Check if there's a quantity input next to this button
            const parent = this.closest('.product-info');
            if (parent) {
                const qtyInput = parent.querySelector('.qty-input');
                if (qtyInput) {
                    quantity = parseInt(qtyInput.value) || 1;
                }
            }
            
            addToCart(productId, quantity);
        });
    });
    
    // Quantity controls
    document.querySelectorAll('.qty-minus').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.productId;
            const input = document.getElementById('qty-' + productId);
            if (input) {
                let val = parseInt(input.value) || 1;
                if (val > 1) input.value = val - 1;
            }
        });
    });
    
    document.querySelectorAll('.qty-plus').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.productId;
            const input = document.getElementById('qty-' + productId);
            if (input) {
                let val = parseInt(input.value) || 1;
                if (val < 99) input.value = val + 1;
            }
        });
    });
    
    // Cart quantity controls
    document.querySelectorAll('.cart-qty-minus').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.productId;
            const input = document.getElementById('cart-qty-' + productId);
            if (input) {
                let val = parseInt(input.value) || 1;
                if (val > 1) {
                    input.value = val - 1;
                    updateCart(productId, parseInt(input.value));
                }
            }
        });
    });
    
    document.querySelectorAll('.cart-qty-plus').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.productId;
            const input = document.getElementById('cart-qty-' + productId);
            if (input) {
                let val = parseInt(input.value) || 1;
                if (val < 99) {
                    input.value = val + 1;
                    updateCart(productId, parseInt(input.value));
                }
            }
        });
    });
    
    // Cart quantity input change
    document.querySelectorAll('.cart-qty-input').forEach(input => {
        input.addEventListener('change', function() {
            const productId = this.id.replace('cart-qty-', '');
            let val = parseInt(this.value) || 1;
            if (val < 1) this.value = 1;
            if (val > 99) this.value = 99;
            updateCart(productId, parseInt(this.value));
        });
    });
    
    // Remove from cart
    document.querySelectorAll('.btn-remove').forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.productId;
            updateCart(productId, 0, 'remove');
        });
    });
});

// Add to Cart function
function addToCart(productId, quantity) {
    fetch('/add-to-cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message);
            updateCartBadge(data.cart_count);
        } else {
            showNotification('Error adding to cart', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Something went wrong', 'error');
    });
}

// Update Cart function
function updateCart(productId, quantity, action = 'update') {
    fetch('/update-cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity,
            action: action
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartBadge(data.cart_count);
            
            // Update subtotal if on cart page
            if (document.querySelector('.cart-summary')) {
                updateCartPage(data);
            }
            
            if (action === 'remove') {
                // Remove item from DOM
                const item = document.querySelector(`.cart-item[data-product-id="${productId}"]`);
                if (item) {
                    item.remove();
                }
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Update cart badge
function updateCartBadge(count) {
    const badge = document.getElementById('cart-badge');
    if (badge) {
        badge.textContent = count;
    }
}

// Update cart page
function updateCartPage(data) {
    const subtotalEl = document.getElementById('cart-subtotal');
    const totalEl = document.getElementById('cart-total');
    
    if (subtotalEl) {
        subtotalEl.textContent = 'RM ' + data.subtotal.toFixed(2);
    }
    if (totalEl) {
        totalEl.textContent = 'RM ' + data.subtotal.toFixed(2);
    }
    
    // Check if cart is empty
    if (data.items.length === 0) {
        location.reload();
    }
}

// Show notification
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    if (!notification) return;
    
    notification.textContent = message;
    notification.style.background = type === 'error' ? '#e85d3a' : '#3d2b1f';
    notification.style.color = type === 'error' ? 'white' : '#f5d742';
    notification.classList.add('show');
    
    clearTimeout(notification.timeout);
    notification.timeout = setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}
