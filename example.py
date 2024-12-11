from danak.base import Model
from danak.fields import (IntegerField, TextField, DateTimeField, 
                         ForeignKey, BooleanField)
from danak.validators import MinLengthValidator, MaxLengthValidator

class User(Model):
    id = IntegerField(primary_key=True)
    username = TextField(nullable=False, unique=True, validators=[
        MinLengthValidator(3),
        MaxLengthValidator(50)
    ])


class Post(Model):
    id = IntegerField(primary_key=True)
    title = TextField(nullable=False, validators=[
        MinLengthValidator(5),
        MaxLengthValidator(200)
    ])
 
def test_create():
    print("\n1. CREATE:")
    # Foydalanuvchi yaratish
    user = User.create(
        username='john_doe',
    )
    print(f"Yaratilgan foydalanuvchi: {user}")

    # Post yaratish
    post = Post.create(
        title='Birinchi post',
    )
    print(f"Yaratilgan post: {post}")

def test_read():
    print("\n2. READ:")
    # Barcha foydalanuvchilarni olish
    users = User.all()
    print("\nBarcha foydalanuvchilar:")
    for user in users:
        print(f"- {user}")

        # ID bo'yicha foydalanuvchini olish
    try:
        user = User.get(id=1)
        print(f"\nID=1 bo'lgan foydalanuvchi: {user}")
    except User.DoesNotExist:
        print("\nID=1 bo'lgan foydalanuvchi topilmadi")

def test_update():
    print("\n3. UPDATE:")
    try:
        # Foydalanuvchini yangilash
        user = User.get(username='john_doe')
        user.username = 'john_doe_updated'
        user.save()
        print(f"Foydalanuvchi yangilandi: {user}")

        # Post yangilash
        post = Post.get(title='Birinchi post')
        post.title = 'Yangilangan post'
        post.save()
        print(f"Post yangilandi: {post}")
    except (User.DoesNotExist, Post.DoesNotExist) as e:
        print(f"Xatolik: {e}")

def test_delete():
    print("\n4. DELETE:")
    try:

        # Foydalanuvchini o'chirish
        user = User.get(username='john_doe_updated')
        user.delete()
        print("Foydalanuvchi o'chirildi")
    except (User.DoesNotExist, Post.DoesNotExist) as e:
        print(f"Xatolik: {e}")

def test_query_operators():
    print("\n5. QUERY OPERATORS:")
    # LIKE operatori
    users = User.filter(username__contains='john')
    print("\nIsmida 'john' bo'lgan foydalanuvchilar:")
    for user in users:
        print(f"- {user}")

def main():
    # Ma'lumotlar bazasiga ulanish
    User.connect('example.db')
    Post.connect('example.db')
    
    # Jadvallarni yaratish
    User.create_table()
    Post.create_table()
    
    try:
        test_create()
        test_read()
        test_update()
        test_delete()
        # test_query_operators()
        
    except Exception as e:
        print(f"\nXato yuz berdi: {e}")

if __name__ == '__main__':
    main()