-- ============================================================
-- TechyAgent: IT Company Support Assistant Database
-- Database: techyagent_db
-- ============================================================

CREATE DATABASE IF NOT EXISTS techyagent_db;
USE techyagent_db;

-- ------------------------------------------------------------
-- 1. Create the software_products table
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS software_products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL UNIQUE,
    category ENUM(
        'CRM',
        'Analytics',
        'Cybersecurity',
        'Collaboration'
    ) NOT NULL,
    base_monthly_price DECIMAL(10,2) NOT NULL
        CHECK (base_monthly_price >= 0),
    product_status ENUM(
        'Active',
        'Maintenance',
        'Retired'
    ) NOT NULL DEFAULT 'Active'
);

-- ------------------------------------------------------------
-- 2. Create the customers table
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(150) NOT NULL,
    industry ENUM(
        'Technology',
        'Finance',
        'Healthcare',
        'Retail',
        'Education',
        'Manufacturing',
        'Other'
    ) NOT NULL DEFAULT 'Other',
    country VARCHAR(80) NOT NULL,
    customer_status ENUM(
        'Active',
        'Inactive'
    ) NOT NULL DEFAULT 'Active'
);

-- ------------------------------------------------------------
-- 3. Create the subscriptions table
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    product_id INT NOT NULL,
    plan ENUM(
        'Starter',
        'Professional',
        'Enterprise'
    ) NOT NULL,
    seats INT NOT NULL CHECK (seats > 0),
    monthly_fee DECIMAL(10,2) NOT NULL
        CHECK (monthly_fee >= 0),
    start_date DATE NOT NULL,
    subscription_status ENUM(
        'Active',
        'Trial',
        'Cancelled',
        'Past Due'
    ) NOT NULL DEFAULT 'Active',

    UNIQUE KEY customer_product_plan (
        customer_id,
        product_id,
        plan
    ),

    CONSTRAINT fk_subscription_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    CONSTRAINT fk_subscription_product
        FOREIGN KEY (product_id)
        REFERENCES software_products(product_id)
);

-- ------------------------------------------------------------
-- 4. Insert sample software products
-- ------------------------------------------------------------
INSERT INTO software_products
    (product_name, category, base_monthly_price, product_status)
VALUES
    ('CRM Platform', 'CRM', 29.00, 'Active'),
    ('Analytics Suite', 'Analytics', 49.00, 'Active'),
    ('Security Suite', 'Cybersecurity', 39.00, 'Active'),
    ('Collaboration Tool', 'Collaboration', 15.00, 'Active'),
    ('Legacy Analytics Tool', 'Analytics', 19.00, 'Maintenance');

-- ------------------------------------------------------------
-- 5. Insert sample business customers
-- ------------------------------------------------------------
INSERT INTO customers
    (company_name, industry, country, customer_status)
VALUES
    ('BrightPath Technologies', 'Technology', 'Bangladesh', 'Active'),
    ('GreenLeaf Retail', 'Retail', 'Bangladesh', 'Active'),
    ('Northstar Finance', 'Finance', 'Singapore', 'Active'),
    ('CareBridge Clinics', 'Healthcare', 'Malaysia', 'Active'),
    ('FutureLearn Academy', 'Education', 'Bangladesh', 'Active'),
    ('Apex Manufacturing', 'Manufacturing', 'India', 'Active'),
    ('PixelCraft Studio', 'Technology', 'United Kingdom', 'Inactive'),
    ('UrbanBasket Ltd', 'Retail', 'Bangladesh', 'Active');

-- ------------------------------------------------------------
-- 6. Insert sample subscriptions
-- Monthly fees are example contract values, not automatically
-- calculated from the product's base monthly price.
-- ------------------------------------------------------------
INSERT INTO subscriptions
    (
        customer_id,
        product_id,
        plan,
        seats,
        monthly_fee,
        start_date,
        subscription_status
    )
VALUES
    (1, 1, 'Professional', 25, 650.00, '2026-01-15', 'Active'),
    (1, 3, 'Enterprise', 25, 900.00, '2026-02-01', 'Active'),
    (2, 1, 'Starter', 8, 180.00, '2026-03-10', 'Active'),
    (2, 4, 'Professional', 20, 240.00, '2026-03-10', 'Active'),
    (3, 2, 'Enterprise', 60, 2400.00, '2025-11-20', 'Active'),
    (3, 3, 'Enterprise', 60, 2100.00, '2025-11-20', 'Active'),
    (4, 3, 'Professional', 18, 540.00, '2026-04-05', 'Trial'),
    (4, 4, 'Starter', 12, 120.00, '2026-04-05', 'Active'),
    (5, 2, 'Professional', 30, 1050.00, '2026-01-08', 'Active'),
    (6, 1, 'Enterprise', 45, 1500.00, '2025-12-01', 'Past Due'),
    (6, 2, 'Professional', 25, 950.00, '2025-12-01', 'Active'),
    (7, 4, 'Starter', 5, 50.00, '2025-09-15', 'Cancelled'),
    (8, 1, 'Professional', 15, 420.00, '2026-05-12', 'Active'),
    (8, 2, 'Starter', 10, 350.00, '2026-05-12', 'Active');

-- ------------------------------------------------------------
-- 7. Quick checks
-- ------------------------------------------------------------
SELECT * FROM software_products;
SELECT * FROM customers;
SELECT * FROM subscriptions;

-- Example business question:
-- What is the monthly recurring revenue (MRR) from active subscriptions?
SELECT SUM(monthly_fee) AS active_monthly_revenue
FROM subscriptions
WHERE subscription_status = 'Active';

-- Example business question:
-- Which products generate the most active subscription revenue?
SELECT
    p.product_name,
    SUM(s.monthly_fee) AS monthly_revenue
FROM subscriptions AS s
JOIN software_products AS p
    ON p.product_id = s.product_id
WHERE s.subscription_status = 'Active'
GROUP BY p.product_id, p.product_name
ORDER BY monthly_revenue DESC;