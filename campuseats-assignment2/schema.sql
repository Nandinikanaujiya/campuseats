-- CS 543 Web Services — Assignment 2
-- CampusEats Relational Schema Definition (PostgreSQL)
-- 
-- Boundary Rule: Each service owns its database tables. No table belongs to more than one service.
-- Decoupled References: Cross-service relations are modeled as UUID attributes instead of hard Foreign Keys.

-- 1. USER SERVICE
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15) NOT NULL,
    user_type VARCHAR(20) NOT NULL CHECK (user_type IN ('customer', 'merchant', 'rider', 'admin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_credentials (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(64) NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE
);


-- 2. CANTEEN (CATALOGUE) SERVICE
CREATE TABLE canteens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    location_desc VARCHAR(255) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE menu_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canteen_id UUID NOT NULL REFERENCES canteens(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    display_order INT DEFAULT 0
);

CREATE TABLE menu_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID NOT NULL REFERENCES menu_categories(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0.00),
    is_available BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- 3. ORDER SERVICE
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL, -- Logical Reference to User Service
    canteen_id UUID NOT NULL,  -- Logical Reference to Canteen Service
    order_status VARCHAR(20) NOT NULL CHECK (order_status IN ('placed', 'preparing', 'ready_for_pickup', 'out_for_delivery', 'delivered', 'cancelled')),
    subtotal DECIMAL(10, 2) NOT NULL CHECK (subtotal >= 0.00),
    service_fee DECIMAL(10, 2) NOT NULL DEFAULT 1.50,
    delivery_fee DECIMAL(10, 2) NOT NULL CHECK (delivery_fee >= 0.00),
    tax DECIMAL(10, 2) NOT NULL CHECK (tax >= 0.00),
    total_price DECIMAL(10, 2) NOT NULL CHECK (total_price >= 0.00),
    ordered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    menu_item_id UUID NOT NULL,   -- Logical Reference to Canteen Service
    item_name VARCHAR(100) NOT NULL, -- Snapshotted name to preserve order history
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price >= 0.00),
    customization_notes TEXT
);


-- 4. DELIVERY SERVICE
CREATE TABLE rider_profiles (
    rider_id UUID PRIMARY KEY, -- Logical Reference to User Service
    current_lat DOUBLE PRECISION,
    current_lng DOUBLE PRECISION,
    rider_status VARCHAR(20) NOT NULL CHECK (rider_status IN ('offline', 'idle', 'delivering')),
    rating DECIMAL(3, 2) DEFAULT 5.00
);

CREATE TABLE delivery_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID UNIQUE NOT NULL, -- Logical Reference to Order Service
    rider_id UUID REFERENCES rider_profiles(rider_id) ON DELETE SET NULL,
    delivery_status VARCHAR(20) NOT NULL CHECK (delivery_status IN ('pending_assignment', 'rider_assigned', 'at_canteen', 'picked_up', 'arrived', 'delivered')),
    dropoff_building VARCHAR(100) NOT NULL,
    delivery_payout DECIMAL(10, 2) NOT NULL CHECK (delivery_payout >= 0.00),
    assigned_at TIMESTAMP WITH TIME ZONE,
    picked_up_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE
);


-- 5. PAYMENT SERVICE
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID UNIQUE NOT NULL, -- Logical Reference to Order Service
    payment_status VARCHAR(20) NOT NULL CHECK (payment_status IN ('pending', 'authorized', 'captured', 'failed', 'refunded')),
    amount DECIMAL(10, 2) NOT NULL CHECK (amount > 0.00),
    payment_method VARCHAR(30) NOT NULL, -- 'campus_card', 'credit_card', 'upi'
    gateway_txn_id VARCHAR(100) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE payment_refunds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    refund_amount DECIMAL(10, 2) NOT NULL CHECK (refund_amount > 0.00),
    reason TEXT NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
