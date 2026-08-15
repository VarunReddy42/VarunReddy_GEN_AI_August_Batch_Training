"""
Q3: Shopping Cart with Default & Mutable Pitfall
--------------------------------------------------
This file demonstrates and then fixes Python's most famous gotcha:
using a MUTABLE object (like a list) as a default argument.
"""


# ===========================================================
# PART A -- Spot the Bug
# ===========================================================
#
# def add_item(item, cart=[]):
#     cart.append(item)
#     return cart
#
# Predicted output of the 4 print() calls:
#
#   print(add_item("apple"))                 -> ['apple']
#   print(add_item("banana"))                -> ['apple', 'banana']
#   print(add_item("milk", cart=["bread"]))   -> ['bread', 'milk']
#   print(add_item("eggs"))                   -> ['apple', 'banana', 'eggs']
#
# WHY this happens:
# In Python, a default argument value (like `cart=[]`) is created only
# ONCE, at the moment the function is *defined* -- not every time the
# function is called. So every call that does NOT pass its own `cart`
# ends up sharing and mutating that SAME list object.
#
#   - Call 1 (no cart passed) -> uses the shared default list -> ['apple']
#   - Call 2 (no cart passed) -> uses the SAME shared list, already has
#     'apple' in it -> ['apple', 'banana']
#   - Call 3 (cart=['bread'] passed) -> uses a brand-new list, so the
#     shared default list is untouched -> ['bread', 'milk']
#   - Call 4 (no cart passed) -> back to the shared default list, which
#     still remembers 'apple' and 'banana' from before -> ['apple',
#     'banana', 'eggs']
#
# This is called the "mutable default argument trap".

def add_item_buggy(item, cart=[]):
    cart.append(item)
    return cart


def demonstrate_part_a():
    print("=== PART A: Buggy Version ===")
    print(add_item_buggy("apple"))
    print(add_item_buggy("banana"))
    print(add_item_buggy("milk", cart=["bread"]))
    print(add_item_buggy("eggs"))
    print()


# ===========================================================
# PART B -- Fix It
# ===========================================================
#
# The fix: use `None` as the default (an immutable sentinel value),
# then create a FRESH list inside the function body every time one
# isn't provided. This way each call that doesn't pass its own cart
# gets its own brand-new list, instead of reusing one shared list.

def add_item(item, cart=None):
    if cart is None:
        cart = []          # a new, independent list every call
    cart.append(item)
    return cart


def demonstrate_part_b():
    print("=== PART B: Fixed Version ===")
    print(add_item("apple"))
    print(add_item("banana"))
    print(add_item("milk", cart=["bread"]))
    print(add_item("eggs"))
    print("(Notice 'apple' and 'banana' each start their own fresh list now)")
    print()


# ===========================================================
# PART C -- Build the Cart
# ===========================================================

def create_cart(owner, discount=0):
    # discount=0 is safe here because 0 is an immutable int.
    # Every call to create_cart() that skips discount gets its own
    # brand-new dict below -- dicts are not shared like the list
    # default was in Part A, because we build the dict fresh inside
    # the function call itself (it's not sitting in the signature).
    return {
        "owner": owner,
        "items": [],
        "discount": discount
    }


def add_to_cart(cart, name, price, qty=1):
    cart["items"].append({
        "name": name,
        "price": price,
        "qty": qty
    })


def update_price(price_tuple, new_price):
    # price_tuple looks like: (item_name, price)
    # Tuples are IMMUTABLE, so we cannot do price_tuple[1] = new_price.
    # Attempting that raises a TypeError, because tuples don't support
    # item assignment once created -- that's the whole point of using
    # a tuple: it guarantees the data can't be changed by accident.
    try:
        price_tuple[1] = new_price
        return price_tuple
    except TypeError as error:
        print("Cannot modify tuple:", error)
        # The correct way to "change" a tuple is to build a new one.
        updated_tuple = (price_tuple[0], new_price)
        print("Instead, created a brand-new tuple:", updated_tuple)
        return updated_tuple


def calculate_total(cart):
    subtotal = 0
    for item in cart["items"]:
        subtotal = subtotal + (item["price"] * item["qty"])

    discount_amount = subtotal * (cart["discount"] / 100)
    final_total = subtotal - discount_amount
    return final_total


def demonstrate_part_c():
    print("=== PART C: Full Shopping Cart Demo ===")

    # Two different customers, two independent carts.
    cart1 = create_cart("Riya", discount=10)
    cart2 = create_cart("Karan")  # discount defaults to 0, safe

    add_to_cart(cart1, "Notebook", 50, qty=3)
    add_to_cart(cart1, "Pen", 10, qty=5)

    add_to_cart(cart2, "Laptop Bag", 1200, qty=1)

    print("Riya's cart:", cart1)
    print("Karan's cart:", cart2)

    # Proof the two carts do NOT share items (Part B's fix at work,
    # since create_cart() builds a new "items": [] on every call):
    print("\nAre the two carts' item lists the same list object?",
          cart1["items"] is cart2["items"])

    print("\nRiya's total (10% discount):", calculate_total(cart1))
    print("Karan's total (no discount):", calculate_total(cart2))

    # Demonstrate the tuple immutability error
    print("\n--- Trying to modify a tuple ---")
    price_info = ("Notebook", 50)
    update_price(price_info, 60)
    print()


# ===========================================================
# Run everything
# ===========================================================
if __name__ == "__main__":
    demonstrate_part_a()
    demonstrate_part_b()
    demonstrate_part_c()


# ===========================================================
# DISCUSSION POINTS
# ===========================================================
#
# Q: Why is discount=0 safe but cart=[] dangerous?
# A: 0 is an immutable int. It can never be changed in place -- any
#    operation on it (like discount += 5) creates a brand-new int and
#    rebinds the name, it never mutates the original 0. A list, on the
#    other hand, IS mutable. cart.append(item) changes the same list
#    object in memory, and since the default list is created only once
#    at function-definition time, every call that skips the argument
#    keeps mutating that one shared list.
#
# Q: What is the difference between rebinding and mutating?
# A: Rebinding means pointing a variable name at a completely new
#    object (e.g. x = x + [1] creates a new list and reassigns x to
#    it). Mutating means changing the contents of the existing object
#    in place, without creating a new one (e.g. x.append(1) changes
#    the same list that x still points to). Rebinding never affects
#    other variables that pointed to the old object; mutating affects
#    every variable that points to that same object.
#
# Q: Which of these are mutable? -- list, tuple, dict, set, str, int
# A: Mutable:   list, dict, set
#    Immutable: tuple, str, int
#
# Q: When you pass a list into a function and modify it, do changes
#    reflect outside? Why?
# A: Yes. Python passes object references by value -- meaning the
#    function parameter is a new name, but it points to the SAME list
#    object as the caller's variable. So methods that mutate in place
#    (append, remove, sort, etc.) are visible outside the function too.
#    Only rebinding the parameter to a new object inside the function
#    (e.g. cart = []) would break that link, because now the parameter
#    points somewhere new while the caller's variable still points to
#    the original object.
