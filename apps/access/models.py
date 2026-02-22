from django.db import models


class Role(models.Model):
    """Роли пользователей: admin, manager, user, guest."""
    name = models.CharField(max_length=50, unique=True, verbose_name='Название роли')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        db_table = 'roles'
        verbose_name = 'Роль'

    def __str__(self):
        return self.name


class UserRole(models.Model):
    """Связь пользователь ↔ роль (у пользователя может быть несколько ролей)."""
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_roles'
        unique_together = [('user', 'role')]
        verbose_name = 'Роль пользователя'


class BusinessElement(models.Model):
    """
    Бизнес-объекты системы, к которым применяются права доступа.
    Примеры: users, products, orders, shops, access_rules
    """
    name = models.CharField(max_length=100, unique=True, verbose_name='Кодовое имя ресурса')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        db_table = 'business_elements'
        verbose_name = 'Бизнес-объект'

    def __str__(self):
        return self.name


class AccessRule(models.Model):
    """
    Правила доступа: роль → бизнес-объект → набор прав.

    Права:
      - read:            читать собственные объекты
      - read_all:        читать все объекты
      - create:          создавать объекты
      - update:          изменять собственные объекты
      - update_all:      изменять все объекты
      - delete:          удалять собственные объекты
      - delete_all:      удалять все объекты
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='access_rules')
    element = models.ForeignKey(BusinessElement, on_delete=models.CASCADE, related_name='access_rules')

    read = models.BooleanField(default=False)
    read_all = models.BooleanField(default=False)
    create = models.BooleanField(default=False)
    update = models.BooleanField(default=False)
    update_all = models.BooleanField(default=False)
    delete = models.BooleanField(default=False)
    delete_all = models.BooleanField(default=False)

    class Meta:
        db_table = 'access_rules'
        unique_together = [('role', 'element')]
        verbose_name = 'Правило доступа'

    def __str__(self):
        return f'{self.role.name} → {self.element.name}'
