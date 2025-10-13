# GitHub Pages Configuration

## 📚 Документация проекта

Этот репозиторий настроен для автоматической публикации документации на GitHub Pages.

### Структура документации

```
docs/
├── index.md              # Главная страница
├── installation.md       # Установка и настройка
├── configuration.md      # Конфигурация
├── deployment.md         # Развертывание
├── api/                  # API документация
│   ├── bot.md           # Bot API
│   ├── admin.md         # Admin API
│   └── webhooks.md      # Webhooks
├── guides/              # Руководства
│   ├── analytics.md     # Аналитика
│   ├── themes.md        # Темы
│   └── calendar.md      # Календарь
└── contributing.md      # Вклад в проект
```

### Настройка GitHub Pages

1. **Включите GitHub Pages:**
   - Перейдите в Settings → Pages
   - Выберите Source: "Deploy from a branch"
   - Выберите Branch: "main" или "gh-pages"

2. **Используйте GitHub Actions:**
   ```yaml
   name: Deploy Documentation
   on:
     push:
       branches: [ main ]
       paths: [ 'docs/**' ]
   
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - name: Deploy to GitHub Pages
           uses: peaceiris/actions-gh-pages@v3
           with:
             github_token: ${{ secrets.GITHUB_TOKEN }}
             publish_dir: ./docs
   ```

### Локальная разработка документации

```bash
# Установите MkDocs
pip install mkdocs mkdocs-material

# Запустите локальный сервер
mkdocs serve

# Соберите документацию
mkdocs build
```

### Автоматическое обновление

Документация автоматически обновляется при:
- Push в main ветку
- Создании новых релизов
- Обновлении файлов в папке `docs/`

### Поддержка

- **Документация:** [iqstocker-cursor.pages.dev](https://iqstocker-cursor.pages.dev)
- **GitHub Pages:** [Настройки Pages](https://github.com/TwinsMinsk/iqstocker-cursor/settings/pages)
