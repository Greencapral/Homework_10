from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)
from django.http import HttpResponse
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy
from store_app.forms import (
    ProductForm,
    CategoryForm,
    ProductDeleteForm,
)
from store_app.tasks import inform_product_creation
from store_app.models import Product, Category


def index(request):
    """
    Отображает главную страницу веб‑приложения.
    Args:
        request (HttpRequest): HTTP‑запрос от клиента.
    Returns:
        HttpResponse: Отрендеренный шаблон главной страницы.
    """
    return render(request, "store_app/main_page.html")


def about(request):
    """
    Отображает страницу «О проекте» веб‑приложения.
    Args:
        request (HttpRequest): HTTP‑запрос от клиента.
    Returns:
        HttpResponse: Отрендеренный шаблон страницы «О нас».
    """
    return render(request, "store_app/about_page.html")


class ProductBaseView:
    """
    Базовый класс для представлений, связанных с товарами.
    Определяет общую модель для всех представлений товаров.
    """

    model = Product  # Модель товара, используемая во всех наследниках


class ProductListView(ProductBaseView, ListView):
    """
    Представление для отображения списка всех товаров.
    """

    context_object_name = (
        "products"  # Ключ в контексте для списка товаров
    )


class ProductDetailView(ProductBaseView, DetailView):
    """
    Представление для отображения подробной информации о конкретном товаре.

    """

    context_object_name = (
        "product"  # Ключ в контексте для объекта товара
    )


class ProductCreateView(ProductBaseView, CreateView):
    """
    Представление для создания нового товара.

    Использует форму ProductForm и перенаправляет на список товаров после успешного создания.
    """

    template_name = "store_app/add_or_edit_prod_or_cat.html"  # Шаблон для создания товара
    context_object_name = (
        "product"  # Ключ в контексте для объекта товара
    )
    form_class = ProductForm  # Форма для создания товара
    extra_context = {
        "title": "Добавление нового товара",  # Заголовок страницы
        "button_name": "Добавить товар",  # Текст на кнопке отправки формы
    }
    success_url = reverse_lazy(
        "products_list"
    )  # URL для перенаправления после успешного создания

    def form_valid(self, form):
        """
        Обработчик успешной валидации формы.
        Переопределяет стандартный метод CreateView.form_valid() для добавления
        дополнительной логики после сохранения товара.

        Args:
            form (ProductForm): валидированная форма с данными товара.

        Returns:
            HttpResponse: HTTP‑ответ, обычно редирект на success_url.
        """
        response = super().form_valid(form)
        # Вызывает родительский метод для выполнения стандартной логики:

        product = form.save()

        inform_product_creation.delay(product.id)
        # Асинхронно запускает задачу Celery для информирования о создании товара.
        # .delay() помещает задачу в очередь Celery — выполнение происходит в фоновом режиме.
        # Передаёт ID товара как параметр для задачи.

        return response
        # Возвращает HTTP‑ответ пользователю (редирект на страницу списка товаров).
        # Выполняется сразу после постановки задачи в очередь — пользователь не ждёт
        # завершения асинхронной задачи.

class ProductUpdateView(ProductBaseView, UpdateView):
    """
    Представление для редактирования существующего товара.

    Использует форму ProductForm и перенаправляет на список товаров после успешного обновления.
    """

    template_name = "store_app/add_or_edit_prod_or_cat.html"  # Шаблон для редактирования товара
    context_object_name = (
        "product"  # Ключ в контексте для объекта товара
    )
    form_class = (
        ProductForm  # Форма для редактирования товара
    )
    extra_context = {
        "title": "Изменение карточки товара",  # Заголовок страницы
        "button_name": "Сохранить изменения",  # Текст на кнопке отправки формы
    }
    success_url = reverse_lazy(
        "products_list"
    )  # URL для перенаправления после успешного обновления


class ProductDeleteView(ProductBaseView, DeleteView):
    """
    Представление для удаления товара.

    Отображает форму подтверждения удаления и перенаправляет на список товаров после удаления.
    """

    template_name = "store_app/product_delete.html"  # Шаблон подтверждения удаления
    form_class = (
        ProductDeleteForm  # Форма подтверждения удаления
    )
    success_url = reverse_lazy(
        "products_list"
    )  # URL для перенаправления после удаления


def categories_list(request):
    """
    Отображает список всех категорий товаров.
    Args:
        request (HttpRequest): HTTP‑запрос от клиента.
    Returns:
        HttpResponse: Отрендеренный шаблон со списком категорий.
    """
    categories = (
        Category.objects.all()
    )  # Получаем все категории из БД
    context = {
        "categories": categories,  # Передаём категории в контекст шаблона
    }
    return render(
        request,
        "store_app/categories_list.html",
        context=context,
    )


def category_add(request):
    """
    Обрабатывает добавление новой категории товаров.
    При POST‑запросе сохраняет новую категорию, при GET‑запросе отображает пустую форму.
    Args:
        request (HttpRequest): HTTP‑запрос от клиента.
    Returns:
        HttpResponse: Отрендеренный шаблон формы добавления категории или перенаправление.
    """
    if request.method == "POST":
        form = CategoryForm(
            request.POST
        )  # Создаём форму с данными из запроса
        if (
            form.is_valid()
        ):  # Проверяем валидность данных формы
            form.save()  # Сохраняем новую категорию в БД
            return redirect(
                "categories_list"
            )  # Перенаправляем на список категорий
    else:
        form = (
            CategoryForm()
        )  # Создаём пустую форму для GET‑запроса
    context = {
        "title": "Добавление новой категории",  # Заголовок страницы
        "button_name": "Добавить категорию",  # Текст на кнопке отправки формы
        "form": form,  # Передаём форму в контекст
    }
    return render(
        request,
        "store_app/add_or_edit_prod_or_cat.html",
        context=context,
    )


def category_edit(request, category_id):
    """
    Обрабатывает редактирование существующей категории товаров.
    При POST‑запросе обновляет категорию, при GET‑запросе отображает форму с текущими данными.
    Args:
        request (HttpRequest): HTTP‑запрос от клиента.
        category_id (int): ID категории для редактирования.
    Returns:
        HttpResponse: Отрендеренный шаблон формы редактирования категории или перенаправление.
    """
    category = get_object_or_404(
        Category, id=category_id
    )  # Получаем категорию или 404
    if request.method == "POST":
        form = CategoryForm(
            request.POST, instance=category
        )  # Создаём форму с данными и экземпляром категории
        if (
            form.is_valid()
        ):  # Проверяем валидность данных формы
            form.save()  # Сохраняем изменения в БД
            return redirect(
                "categories_list"
            )  # Перенаправляем на список категорий
    else:
        form = CategoryForm(
            instance=category
        )  # Создаём форму с текущими данными категории
    context = {
        "title": "Изменение категории",  # Заголовок страницы
        "button_name": "Сохранить изменения",  # Текст на кнопке отправки формы
        "form": form,  # Передаём форму в контекст
    }
    return render(
        request,
        "store_app/add_or_edit_prod_or_cat.html",
        context=context,
    )
