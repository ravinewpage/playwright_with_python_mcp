# Kohls.com Page Structure & Locators

## Page Map

### 1. HomePage
- **URL:** `https://www.kohls.com/`
- **Purpose:** Entry point, navigation menu
- **Key Elements:**
  - Logo: `[data-testid="kohls-logo"]`
  - Search box: `input[placeholder="Search"]`
  - Sign In link: `a[href*="signin"]`
  - Categories menu: `button[aria-label="Shop by Category"]`

### 2. LoginPage
- **URL:** `https://www.kohls.com/myaccount/signin.jsp`
- **Purpose:** User authentication
- **Key Elements:**
  - Email input: `[data-testid="email-input"]`
  - Password: **MANUAL PAUSE** (never automate)
  - Sign In button: `button[type="submit"]`
  - Error message: `[data-testid="error-message"]`
  - Success indicator: Account menu visible

### 3. SearchPage
- **URL:** `https://www.kohls.com/search?query=...`
- **Purpose:** Product catalog browsing
- **Key Elements:**
  - Search results: `.product-tile`
  - Product link: `a[data-testid="product-link"]`
  - Price: `[data-testid="product-price"]`
  - Filter sidebar: `aside[data-testid="filters"]`

### 4. ProductPage
- **URL:** `https://www.kohls.com/product/prd-...`
- **Purpose:** Single product details
- **Key Elements:**
  - Product name: `h1[data-testid="product-title"]`
  - Price: `[data-testid="price"]`
  - Size selector: `select[data-testid="size-select"]`
  - Color selector: `fieldset[data-testid="color-option"]`
  - Quantity: `input[data-testid="quantity"]`
  - Add to Cart: `button[data-testid="add-to-cart"]`
  - Popup: `.added-to-cart-modal`

### 5. CartPage
- **URL:** `https://www.kohls.com/cart`
- **Purpose:** Review items before checkout
- **Key Elements:**
  - Cart items: `.cart-item`
  - Item price: `[data-testid="item-price"]`
  - Subtotal: `[data-testid="cart-subtotal"]`
  - Proceed to Checkout: `button[data-testid="checkout-button"]`
  - Remove item: `button[aria-label="Remove"]`

### 6. CheckoutPage
- **URL:** `https://www.kohls.com/checkout`
- **Purpose:** Shipping, billing, payment entry
- **Key Elements:**
  - Email: `input[data-testid="email"]`
  - First name: `input[data-testid="firstName"]`
  - Last name: `input[data-testid="lastName"]`
  - Address: `input[data-testid="address"]`
  - City: `input[data-testid="city"]`
  - State: `select[data-testid="state"]`
  - ZIP: `input[data-testid="zip"]`
  - CVV: **MANUAL PAUSE** (never automate)
  - Expiry: **MANUAL PAUSE** (never automate)
  - Review Order: `button[data-testid="review-order"]`
  - Place Order: **NEVER CLICK** (stops test here)

### 7. OrderConfirmationPage
- **URL:** Displayed after place order (NOT REACHED in our tests)
- **Elements:**
  - Thank you message: `h1:contains("Thank you")`
  - Order ID: `[data-testid="order-number"]`

## Dynamic Elements
- Shopping cart count: Updates via AJAX (use `wait_for_load_state()`)
- Prices: May vary by location/promotion (use assertions with thresholds)
- Out of stock: May change (validate before adding to cart)

## API Endpoints (Captured in network_log)
- `/api/commerce/v1/search` - Product search
- `/api/commerce/v1/cart` - Cart operations
- `/api/commerce/v1/checkout` - Checkout flow
- `/api/commerce/v1/orders` - Order placement (NOT called in our tests)
