"""
One-time fix for the InconsistentMigrationHistory error from 2026-08-07.

What happened: products/cart/orders 0001_initial migrations were applied
to the database in their *original* (non-store-scoped) form, then rewritten
in place to add a dependency on stores.0004_store_ecommerce_fields (added
afterward). Django now sees products.0001_initial recorded as applied
before a dependency that was never applied, which blocks every
manage.py makemigrations/migrate command.

This script drops the (empty, same-day test) products/cart/orders tables
and clears their migration history rows, so a normal `migrate` can
recreate them cleanly from the current (correct) migration files.

Run from the rekjrc/ directory, inside your venv:
    python fix_migration_20260807.py

It will show you exactly what it's about to run and ask you to type DROP
to confirm before touching anything. Safe to delete once you've run it.
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rekjrc.settings")
django.setup()

from django.db import connection

DROP_TABLES = [
    "orders_orderitem",
    "orders_order",
    "cart_cartitem",
    "cart_cart",
    "products_productvariant",
    "products_productimage",
    "products_product",
]

def main():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = ANY(%s)
        """, [DROP_TABLES])
        existing = {row[0] for row in cursor.fetchall()}

        cursor.execute(
            "SELECT app, name FROM django_migrations WHERE app IN ('products', 'cart', 'orders') ORDER BY app, name"
        )
        migration_rows = cursor.fetchall()

    print("This will run:\n")
    for t in DROP_TABLES:
        if t in existing:
            print(f"  DROP TABLE IF EXISTS {t} CASCADE;")
        else:
            print(f"  -- {t} doesn't exist yet, skipping")
    if migration_rows:
        print("\nAnd remove these django_migrations rows:")
        for app, name in migration_rows:
            print(f"  {app}.{name}")
    else:
        print("\n(No products/cart/orders rows found in django_migrations -- nothing to remove there.)")

    if not existing and not migration_rows:
        print("\nNothing to do -- database already clean. You can just run migrate.bat / _migrations.bat now.")
        return

    print("\nIf any of these tables actually contain rows you care about, stop now and tell Jason's Claude session instead of typing DROP.")
    confirm = input("\nType DROP to proceed: ").strip()
    if confirm != "DROP":
        print("Aborted -- nothing changed.")
        return

    with connection.cursor() as cursor:
        for t in DROP_TABLES:
            if t in existing:
                cursor.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")
        cursor.execute("DELETE FROM django_migrations WHERE app IN ('products', 'cart', 'orders');")

    print("\nDone. Now run _migrations.bat (or `python manage.py makemigrations` then `migrate`) again.")

if __name__ == "__main__":
    main()
