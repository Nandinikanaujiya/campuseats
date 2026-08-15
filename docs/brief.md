# CampusEats Brief

## What

CampusEats is a campus food ordering and delivery system. Students can log in,
manage their profile and delivery addresses, browse campus restaurants and their
menus, add food items to a cart, and place an order. They can pay online and
track the delivery of their food. A rider is assigned to deliver the order.
The system also sends notifications when the order is placed, paid, on the way,
and delivered.

The system is organized around six main services: Accounts, Catalogue, Orders,
Payments, Delivery, and Notifications. Each service has its own responsibility
and owns its own data.

## Who

The main user and participants in CampusEats are:

- Students - use the system to browse food, manage their account, place orders,
  make payments, and track deliveries.
- Riders - are assigned to orders and deliver the food.
- Campus restaurants - provide restaurants, menus, food items, and prices
  through the catalogue.
- CampusEats services - work together to manage accounts, catalogue information,
  orders, payments, delivery, and notifications.

## Nouns

The main nouns in the CampusEats system are:

- Student
- User
- Profile
- Address
- Restaurant
- Menu
- Food item
- Price
- Cart
- Order
- Order status
- Payment
- Transaction
- Refund
- Rider
- Delivery
- Assignment
- Notification
- Message log

The six main service nouns are:

- Accounts
- Catalogue
- Orders
- Payments
- Delivery
- Notifications

Their owned data is:

- Accounts - users, addresses, login
- Catalogue - restaurants, menus, prices
- Orders - carts, orders, status
- Payments - transactions, refunds
- Delivery - riders, assignments
- Notifications - message log

## Verbs

The main verbs in the CampusEats system are:

- Log in
- Manage profile
- Manage addresses
- Browse restaurants
- Browse menus
- Add to cart
- Place order
- Pay
- Refund
- Assign rider
- Deliver
- Track delivery
- Send notification
- Add item to cart
- Get order
- Cancel order
- List restaurants
- Get menu
- Check item
- Charge payment

Some important service operations are:

- `addToCart`
- `placeOrder`
- `getOrder`
- `cancelOrder`
- `listRestaurants`
- `getMenu`
- `checkItem`

## Summary

CampusEats connects students with campus food services for ordering and
delivery. The system separates its responsibilities into Accounts, Catalogue,
Orders, Payments, Delivery, and Notifications. Each service owns a distinct
part of the data and communicates with other services through defined
operations or contracts rather than directly accessing another service's
internal data.
