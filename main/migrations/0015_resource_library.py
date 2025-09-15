from django.db import migrations, models
import main.models.resource
from django.conf import settings
import django.db.models.deletion
from django.utils.text import slugify


def seed_default_categories(apps, schema_editor):
    Category = apps.get_model('main', 'ResourceCategory')
    defaults = [
        'English',
        'History',
        'Life Science',
        'Physics',
        'Geography',
    ]
    for name in defaults:
        category, created = Category.objects.get_or_create(name=name)
        if created:
            base = slugify(name) or 'category'
            slug = base
            idx = 2
            while Category.objects.filter(slug=slug).exclude(pk=category.pk).exists():
                slug = f"{base}-{idx}"
                idx += 1
            category.slug = slug
            category.save(update_fields=['slug'])


def remove_default_categories(apps, schema_editor):
    Category = apps.get_model('main', 'ResourceCategory')
    Category.objects.filter(name__in=[
        'English',
        'History',
        'Life Science',
        'Physics',
        'Geography',
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_merge_0002_add_created_by_0013_game_points'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResourceCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('slug', models.SlugField(blank=True, max_length=220, unique=True)),
                ('name', models.CharField(max_length=150, unique=True)),
                ('description', models.TextField(blank=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_resource_categories', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ResourceDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('term', models.CharField(choices=[('term1', 'Term 1'), ('term2', 'Term 2'), ('term3', 'Term 3'), ('term4', 'Term 4'), ('other', 'Supplementary'), ('atp', 'Annual Teaching Plan'), ('past_papers', 'Past Papers')], default='other', max_length=20)),
                ('file', models.FileField(upload_to=main.models.resource.resource_upload_to)),
                ('original_filename', models.CharField(blank=True, max_length=255)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='main.resourcecategory')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploaded_resource_documents', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['title'],
            },
        ),
        migrations.RunPython(seed_default_categories, remove_default_categories),
    ]
