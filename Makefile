.PHONY: setup redis run worker server clean

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

venv:
	@if [ ! -d "venv" ]; then \
		echo "Создание виртуального окружения..."; \
		uv venv venv; \
	else \
		echo "Виртуальное окружение уже существует"; \
	fi

# Синхронизация зависимостей через uv sync
uv-sync: venv
	@echo "Синхронизация зависимостей с помощью uv sync..."; \
	uv sync --python venv/bin/python

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


# Запуск Celery worker через модуль Python (обход проблемы с shebang)
worker: uv-sync
	@echo "Запуск Celery worker через python -m..."; \
	./venv/bin/python -m celery -A config worker --pool=solo

server:
	@echo "Запуск Django development server..."; \
	. venv/bin/activate && \
	python manage.py runserver & \
	echo $$! > server.pid

clean:
	@echo "Очистка окружения..."; \
	# Останавливаем процессы по PID
	if [ -f "celery.pid" ]; then kill $$(cat celery.pid) 2>/dev/null || true; rm -f celery.pid; fi; \
	if [ -f "server.pid" ]; then kill $$(cat server.pid) 2>/dev/null || true; rm -f server.pid; fi; \
	# Останавливаем Redis
	docker stop redis-server 2>/dev/null || true; \
#	docker rm redis-server 2>/dev/null || true; \
	# Удаляем виртуальное окружение и PID‑файлы
	rm -rf venv; \
	echo "Очистка завершена."