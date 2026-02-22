"""
python manage.py seed_data

Заполняет БД тестовыми данными:
  - Роли: admin, manager, user, guest
  - Бизнес-объекты: products, orders, shops, users, access_rules
  - Правила доступа для каждой роли
  - Тестовые пользователи
"""
from django.core.management.base import BaseCommand
from apps.users.models import User
from apps.users.utils import hash_password
from apps.access.models import Role, BusinessElement, AccessRule, UserRole


ROLES = [
    {'name': 'admin', 'description': 'Полный доступ ко всем ресурсам'},
    {'name': 'manager', 'description': 'Управление товарами, заказами, магазинами'},
    {'name': 'user', 'description': 'Базовый пользователь — работает со своими объектами'},
    {'name': 'guest', 'description': 'Только чтение публичных данных'},
]

ELEMENTS = [
    {'name': 'products', 'description': 'Товары'},
    {'name': 'orders', 'description': 'Заказы'},
    {'name': 'shops', 'description': 'Магазины'},
    {'name': 'users', 'description': 'Пользователи'},
    {'name': 'access_rules', 'description': 'Правила доступа'},
]

# role_name → element_name → права
ACCESS_MATRIX = {
    'admin': {
        'products':     dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=True, delete_all=True),
        'orders':       dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=True, delete_all=True),
        'shops':        dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=True, delete_all=True),
        'users':        dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=True, delete_all=True),
        'access_rules': dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=True, delete_all=True),
    },
    'manager': {
        'products':     dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=False, delete_all=False),
        'orders':       dict(read=True, read_all=True, create=True, update=True, update_all=True, delete=False, delete_all=False),
        'shops':        dict(read=True, read_all=True, create=True, update=True, update_all=False, delete=False, delete_all=False),
        'users':        dict(read=True, read_all=True, create=False, update=False, update_all=False, delete=False, delete_all=False),
        'access_rules': dict(read=True, read_all=True, create=False, update=False, update_all=False, delete=False, delete_all=False),
    },
    'user': {
        'products':     dict(read=True, read_all=False, create=True, update=True, update_all=False, delete=True, delete_all=False),
        'orders':       dict(read=True, read_all=False, create=True, update=True, update_all=False, delete=True, delete_all=False),
        'shops':        dict(read=True, read_all=False, create=False, update=False, update_all=False, delete=False, delete_all=False),
        'users':        dict(read=True, read_all=False, create=False, update=False, update_all=False, delete=False, delete_all=False),
        'access_rules': dict(read=False, read_all=False, create=False, update=False, update_all=False, delete=False, delete_all=False),
    },
    'guest': {
        'products':     dict(read=True, read_all=True, create=False, update=False, update_all=False, delete=False, delete_all=False),
        'orders':       dict(read=False, read_all=False, create=False, update=False, update_all=False, delete=False, delete_all=False),
        'shops':        dict(read=True, read_all=True, create=False, update=False, update_all=False, delete=False, delete_all=False),
        'users':        dict(read=False, read_all=False, create=False, update=False, update_all=False, delete=False, delete_all=False),
        'access_rules': dict(read=False, read_all=False, create=False, update=False, update_all=False, delete=False, delete_all=False),
    },
}

TEST_USERS = [
    {'first_name': 'Админ', 'last_name': 'Системный', 'patronymic': 'Главный',
     'email': 'admin@example.com', 'password': 'admin123', 'role': 'admin'},
    {'first_name': 'Иван', 'last_name': 'Менеджеров', 'patronymic': 'Петрович',
     'email': 'manager@example.com', 'password': 'manager123', 'role': 'manager'},
    {'first_name': 'Пётр', 'last_name': 'Пользователев', 'patronymic': 'Иванович',
     'email': 'user@example.com', 'password': 'user1234', 'role': 'user'},
    {'first_name': 'Гость', 'last_name': 'Гостевой', 'patronymic': '',
     'email': 'guest@example.com', 'password': 'guest123', 'role': 'guest'},
]


class Command(BaseCommand):
    help = 'Заполняет БД тестовыми данными для демонстрации системы'

    def handle(self, *args, **options):
        self.stdout.write('Создание ролей...')
        roles = {}
        for r in ROLES:
            role, created = Role.objects.get_or_create(name=r['name'], defaults={'description': r['description']})
            roles[role.name] = role
            self.stdout.write(f'  {"Создана" if created else "Уже есть"}: {role.name}')

        self.stdout.write('Создание бизнес-объектов...')
        elements = {}
        for e in ELEMENTS:
            el, created = BusinessElement.objects.get_or_create(name=e['name'], defaults={'description': e['description']})
            elements[el.name] = el
            self.stdout.write(f'  {"Создан" if created else "Уже есть"}: {el.name}')

        self.stdout.write('Создание правил доступа...')
        for role_name, element_rules in ACCESS_MATRIX.items():
            role = roles[role_name]
            for element_name, perms in element_rules.items():
                element = elements[element_name]
                rule, created = AccessRule.objects.get_or_create(
                    role=role, element=element,
                    defaults=perms
                )
                if not created:
                    for k, v in perms.items():
                        setattr(rule, k, v)
                    rule.save()
                self.stdout.write(f'  {role_name} → {element_name}: OK')

        self.stdout.write('Создание тестовых пользователей...')
        for ud in TEST_USERS:
            user, created = User.objects.get_or_create(
                email=ud['email'],
                defaults={
                    'first_name': ud['first_name'],
                    'last_name': ud['last_name'],
                    'patronymic': ud['patronymic'],
                    'password_hash': hash_password(ud['password']),
                }
            )
            role = roles[ud['role']]
            UserRole.objects.get_or_create(user=user, role=role)
            status_str = 'Создан' if created else 'Уже есть'
            self.stdout.write(f'  {status_str}: {user.email} (роль: {ud["role"]}, пароль: {ud["password"]})')

        self.stdout.write(self.style.SUCCESS('\n✅ Тестовые данные успешно загружены!'))
        self.stdout.write('\nТестовые аккаунты:')
        for ud in TEST_USERS:
            self.stdout.write(f'  {ud["role"]:10} | {ud["email"]:30} | пароль: {ud["password"]}')
