import os
from celery import Celery

# Устанавливает переменную окружения DJANGO_SETTINGS_MODULE, указывающую на модуль настроек Django.
# Это необходимо для того, чтобы Celery мог получить доступ к настройкам проекта Django.
# Значение 'config.settings' соответствует расположению файла настроек в проекте.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


# Создаёт экземпляр приложения Celery с именем 'config'.
# Имя приложения используется для идентификации в кластере Celery и в логах.
app = Celery('config')

# Загружает конфигурацию Celery из настроек Django.
# Параметры:
#   - 'django.conf:settings' — указывает, откуда загружать настройки (модуль django.conf, объект settings);
#   - namespace='CELERY' — задаёт префикс для параметров конфигурации Celery в настройках Django.
#     Это означает, что все настройки Celery должны быть сгруппированы под префиксом CELERY_ в файле настроек Django,
#     (например, CELERY_BROKER_URL, CELERY_RESULT_BACKEND и т.д.).
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживает и регистрирует задачи Celery в проекте.
# Механизм ищет файлы tasks.py во всех приложениях Django и регистрирует найденные задачи.
# Это упрощает управление задачами: не требуется вручную перечислять и импортировать каждую задачу.
app.autodiscover_tasks()
