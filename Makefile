.PHONY: setup redis run worker server clean install-uv

setup: install-uv venv uv-sync

# Установка uv, если не найден
install-uv:
	@if ! command -v uv &> /dev/null; then \
		echo "Утилита uv не найдена, выполняется установка..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		export PATH="$HOME/.local/bin:$${PATH}"; \
		echo "uv установлен успешно."; \
	else \
		echo "Утилита uv уже установлена."; \
	fi

# Создание виртуального окружения с помощью uv
venv:
	@if [ ! -d "venv" ]; then \
		echo "Создание виртуального окружения..."; \
		uv venv venv --python=/opt/hostedtoolcache/Python/3.14.3/x64/bin/python3; \
	else \
		echo "Виртуальное окружение уже существует"; \
	fi

# Синхронизация зависимостей через uv sync с явным указанием окружения и без создания .venv
uv-sync: venv
	@if [ ! -f "pyproject.toml" ] && [ ! -f "requirements.txt" ]; then \
		echo "Ошибка: не найден pyproject.toml или requirements.txt"; \
		exit 1; \
	fi; \
	echo "Синхронизация зависимостей с помощью uv sync..."; \
	uv sync --python venv/bin/python --no-install-workspace

# Запуск Redis-контейнера (с проверкой существования и состояния)
redis:
	@if docker ps -a --format "{{.Names}}" | grep -q "^redis-server$$"; then \
		if docker inspect -f '{{.State.Running}}' redis-server 2>/dev/null | grep -q "true"; then \
			echo "Контейнер redis-server уже запущен"; \
	else \
		echo "Контейнер redis-server остановлен, выполняется запуск..."; \
		docker start redis-server; \
	fi; \
	else \
		echo "Контейнер redis-server не найден, выполняется создание..."; \
		docker run -d --name redis-server -p 6379:6379 redis; \
	fi

# Запуск Celery worker с диагностикой и без использования @echo в shell-командах
worker: uv-sync
	echo "Запуск Celery worker..."; \
	echo "Проверка доступности Celery в окружении..."; \
	if ! ./venv/bin/python -c "import celery; print(f'Celery {celery.__version__} доступен')" 2>/dev/null; then \
		echo "Ошибка: Celery не найден в виртуальном окружении"; \
		echo "Содержимое venv/lib/python3.14/site-packages/:"; \
		ls -la ./venv/lib/python3.14/site-packages/ 2>/dev/null || echo "Папка site-packages не найдена"; \
		echo "Полный список установленных пакетов:"; \
		if [ -f "./venv/bin/pip" ]; then \
			./venv/bin/pip list 2>/dev/null || echo "pip не может вывести список пакетов"; \
	else \
			echo "pip не найден в виртуальном окружении"; \
	fi; \
		exit 1; \
	fi; \
	./venv/bin/python -m celery -A config worker --pool=solo

# Запуск Django development server
server: uv-sync
	echo "Запуск Django development server..."; \
	./venv/bin/python manage.py runserver

# Комбинированная цель для запуска всего стека
run: uv-sync redis
	echo "Полный стек запущен: зависимости установлены, Redis работает."
	echo "Запустите make worker и make server в отдельных терминалах."

# Очистка: остановка и удаление Redis-контейнера, удаление виртуального окружения
clean:
	echo "Очистка окружения..."; \
	docker stop redis-server 2>/dev/null || true; \
	docker rm redis-server 2>/dev/null || true; \
	pkill -f "python manage.py runserver" 2>/dev/null || true; \
	pkill -f "celery -A config worker" 2>/dev/null || true; \
	rm -rf venv .venv; \
	echo "Очистка завершена."
