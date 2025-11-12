from django.core.management.base import BaseCommand
from django.utils.text import slugify
from shops.models import Category


class Command(BaseCommand):
    help = 'Seed initial categories for cloth marketplace'

    def handle(self, *args, **kwargs):
        categories_data = [
            # Main categories
            {'name': 'Mens Wear', 'parent': None},
            {'name': 'Womens Wear', 'parent': None},
            {'name': 'Kids Wear', 'parent': None},
            {'name': 'Traditional Wear', 'parent': None},
            {'name': 'Western Wear', 'parent': None},

            # Men's subcategories
            {'name': 'Shirts', 'parent': 'Mens Wear'},
            {'name': 'T-Shirts', 'parent': 'Mens Wear'},
            {'name': 'Jeans', 'parent': 'Mens Wear'},
            {'name': 'Trousers', 'parent': 'Mens Wear'},
            {'name': 'Kurtas', 'parent': 'Mens Wear'},

            # Women's subcategories
            {'name': 'Sarees', 'parent': 'Womens Wear'},
            {'name': 'Kurtis', 'parent': 'Womens Wear'},
            {'name': 'Salwar Suits', 'parent': 'Womens Wear'},
            {'name': 'Lehenga', 'parent': 'Womens Wear'},
            {'name': 'Tops', 'parent': 'Womens Wear'},
            {'name': 'Jeans', 'parent': 'Womens Wear'},
            {'name': 'Dresses', 'parent': 'Womens Wear'},

            # Kids subcategories
            {'name': 'Boys Clothing', 'parent': 'Kids Wear'},
            {'name': 'Girls Clothing', 'parent': 'Kids Wear'},
            {'name': 'Baby Clothing', 'parent': 'Kids Wear'},
        ]

        parent_categories = {}

        # Create parent categories first
        for cat_data in categories_data:
            if cat_data['parent'] is None:
                cat, created = Category.objects.get_or_create(
                    name=cat_data['name'],
                    defaults={'slug': slugify(cat_data['name'])}
                )
                parent_categories[cat_data['name']] = cat
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created category: {cat.name}'))

        # Create subcategories
        for cat_data in categories_data:
            if cat_data['parent'] is not None:
                parent = parent_categories.get(cat_data['parent'])
                if parent:
                    cat, created = Category.objects.get_or_create(
                        name=cat_data['name'],
                        parent=parent,
                        defaults={'slug': slugify(f"{parent.slug}-{cat_data['name']}")}
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Created subcategory: {cat.name} under {parent.name}'))

        self.stdout.write(self.style.SUCCESS(f'\nTotal categories: {Category.objects.count()}'))