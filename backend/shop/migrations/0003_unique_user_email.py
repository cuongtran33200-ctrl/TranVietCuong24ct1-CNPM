from django.db import migrations


class Migration(migrations.Migration):
    """Chặn email trùng ở database, không phân biệt hoa thường.

    Cột `email` của auth_user là NOT NULL nên không đổi giá trị. Thay vào đó thêm
    cột sinh `email_lower` = email viết thường, và đặt UNIQUE lên cột này.
    Email rỗng/chỉ có khoảng trắng được chuyển thành NULL trong cột sinh, mà
    MySQL cho phép nhiều NULL trong chỉ mục UNIQUE nên không bị chặn.
    """

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("shop", "0002_alter_product_image"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE auth_user "
                "ADD COLUMN email_lower VARCHAR(254) "
                "GENERATED ALWAYS AS (NULLIF(LOWER(TRIM(email)), '')) STORED, "
                "ADD UNIQUE INDEX unique_user_email_lower (email_lower);"
            ),
            reverse_sql=(
                "ALTER TABLE auth_user "
                "DROP INDEX unique_user_email_lower, "
                "DROP COLUMN email_lower;"
            ),
        ),
    ]
