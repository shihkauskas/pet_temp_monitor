# Монитор температуры

Инструмент на Python для мониторинга температуры процессора на Linux с использованием `lm-sensors`. Логирует данные, отправляет уведомления в Telegram и предоставляет веб-интерфейс с графиками. Работает как два systemd-сервиса от пользователя `pet-temp`.

## Описание

Проект состоит из двух компонентов:
- **temp_monitor_core.py**: Отслеживает температуру процессора (ядро 0), записывает данные в лог-файл с ротацией и отправляет уведомления в Telegram:
  - При превышении порога (`65°C` по умолчанию) — алерт с 🚨.
  - При возврате к норме (≤ `60°C` по умолчанию) — сообщение о восстановлении с ✅.
- **temp_monitor_web.py**: Flask-сервер, который читает логи и отображает интерактивный график температуры за последние 7 дней (Chart.js, Tailwind CSS).

Логи хранятся в `/opt/pet_temp/logs/temp_monitor.log` с ротацией (макс. 10 МБ, 5 резервных копий).

## Скриншот

Веб-интерфейс с графиком температуры:

![График температуры](web_page.png)

## Возможности
- Периодическая проверка температуры через `lm-sensors`.
- Логирование в файл с ротацией.
- Уведомления в Telegram о превышении температуры и восстановлении.
- Веб-интерфейс с графиком температуры (зум, тултипы, без года в метках времени).
- Настраиваемые пороги и интервалы проверки.
- Запуск как systemd-сервисы от пользователя `pet-temp`.

## Требования
- Linux-система (протестировано на Ubuntu/Debian).
- Python 3.6+.
- `lm-sensors` для чтения температуры.
- Токен Telegram-бота и ID чата для уведомлений.

## Установка через Docker

1. **Скачайте образ**:
   - Либо с Docker Hub:
     ```bash
     docker pull shihkauskas/pet-temp-monitor:1.0.0
     ```
   - Либо соберите локально:
     ```bash
     git clone https://github.com/shihkauskas/pet_temp_monitor.git
     cd pet_temp_monitor
     docker build -t shihkauskas/pet-temp-monitor:1.0.0 .
     ```
2. **Запустите контейнер**:
   - Пример с volume для логов:
     ```bash
     mkdir -p ~/pet_temp_logs
     docker run -d \
       --name pet-temp-monitor \
       --device /dev/i2c-1 \
       -v ~/pet_temp_logs:/opt/pet_temp/logs \
       -p 8080:8080 \
       shihkauskas/pet-temp-monitor:1.0.0
     ```
   - **Пояснение**:
     - `--device /dev/i2c-1`: Даёт доступ к `lm-sensors` (проверь устройство с `ls /dev/i2c*`).
     - `-v ~/pet_temp_logs:/opt/pet_temp/logs`: Монтирует логи на хост в `~/pet_temp_logs`.
     - `-p 8080:8080`: Пробрасывает порт веб-интерфейса.

## Установка через DEB-пакет

1. **Установите базовые зависимости**:
   ```bash
   sudo apt update
   sudo apt install python3 python3-venv lm-sensors
   ```
2. **Скачайте DEB-пакет**:
   - Загрузите `pet-temp-monitor_1.1.0.deb` из [релизов](https://github.com/yourusername/temperature-monitor/releases) или соберите самостоятельно (см. ниже).
3. **Установите пакет**:
   ```bash
   sudo dpkg -i pet-temp-monitor_1.1.0.deb
   ```
   Если возникают ошибки с зависимостями, используйте:
   ```bash
   sudo dpkg -i --force-depends pet-temp-monitor_1.1.0.deb
   sudo apt-get install -f
   ```
   Пакет автоматически:
   - Установит зависимости через `pip` (`requests==2.32.3`, `python-dateutil==2.9.0`, `flask==3.0.3`).
   - Создаст пользователя `pet-temp` без логина.
   - Настроит директории `/opt/pet_temp` и `/opt/pet_temp/logs`.
   - Создаст виртуальное окружение `/opt/pet_temp/venv`.
   - Настроит права доступа.
   - Установит и запустит systemd-сервисы (`pet-temp-monitor`, `pet-temp-web`).
4. **Настройте Telegram**:
   - Отредактируйте `/opt/pet_temp/temp_monitor_core.py`:
     ```python
     TELEGRAM_TOKEN = 'YOUR_BOT_TOKEN'  # Получите через @BotFather
     TELEGRAM_CHAT_ID = 'YOUR_CHAT_ID'  # ID вашего чата
     ```
   - Перезапустите сервис:
     ```bash
     sudo systemctl restart pet-temp-monitor
     ```
5. **Проверьте**:
   - Логи: `/opt/pet_temp/logs/temp_monitor.log`.
   - Уведомления в Telegram: при температуре > 65°C (🚨) и ≤ 60°C (✅).
   - Веб-интерфейс: http://localhost:8080 (график без года в метках).
   - Статус сервисов:
     ```bash
     systemctl status pet-temp-monitor
     systemctl status pet-temp-web
     ```

## Ручная установка (альтернатива)

### Шаг 1: Установка lm-sensors
```bash
sudo apt update
sudo apt install lm-sensors
```
Проверьте:
```bash
sensors
```
Найдите строку, например, `Core 0: +45.0°C`. Измените `get_temperature()` в `/opt/pet_temp/temp_monitor_core.py`, если нужен другой сенсор.

### Шаг 2: Создание пользователя pet-temp
```bash
sudo useradd -r -s /bin/false pet-temp
```

### Шаг 3: Клонирование репозитория
```bash
git clone https://github.com/shihkauskas/pet_temp_monitor.git
sudo mkdir -p /opt/pet_temp/logs
sudo mv temperature-monitor/temp_monitor_core.py /opt/pet_temp/
sudo mv temperature-monitor/temp_monitor_web.py /opt/pet_temp/
sudo mv temperature-monitor/requirements.txt /opt/pet_temp/
```
Настройте права:
```bash
sudo chown -R pet-temp:pet-temp /opt/pet_temp
sudo chmod -R 755 /opt/pet_temp
sudo chmod -R 775 /opt/pet_temp/logs
```

### Шаг 4: Настройка виртуального окружения
```bash
sudo python3 -m venv /opt/pet_temp/venv
sudo /opt/pet_temp/venv/bin/pip install -r /opt/pet_temp/requirements.txt
sudo chown -R pet-temp:pet-temp /opt/pet_temp/venv
```

### Шаг 5: Настройка скриптов
Отредактируйте `/opt/pet_temp/temp_monitor_core.py`:
```python
TELEGRAM_TOKEN = 'YOUR_BOT_TOKEN'
TELEGRAM_CHAT_ID = 'YOUR_CHAT_ID'
```

### Шаг 6: Тестирование
```bash
sudo -u pet-temp /opt/pet_temp/venv/bin/python /opt/pet_temp/temp_monitor_core.py
sudo -u pet-temp /opt/pet_temp/venv/bin/python /opt/pet_temp/temp_monitor_web.py
```

### Шаг 7: Настройка systemd-сервисов
Создайте:
```bash
sudo nano /etc/systemd/system/pet-temp-monitor.service
```
Добавьте:
```
[Unit]
Description=Сервис мониторинга температуры Pet Temp
After=network.target

[Service]
User=pet-temp
Group=pet-temp
ExecStart=/opt/pet_temp/venv/bin/python /opt/pet_temp/temp_monitor_core.py
Restart=always

[Install]
WantedBy=multi-user.target
```
Создайте:
```bash
sudo nano /etc/systemd/system/pet-temp-web.service
```
Добавьте:
```
[Unit]
Description=Веб-интерфейс мониторинга температуры Pet Temp
After=network.target

[Service]
User=pet-temp
Group=pet-temp
ExecStart=/opt/pet_temp/venv/bin/python /opt/pet_temp/temp_monitor_web.py
Restart=always

[Install]
WantedBy=multi-user.target
```
Активируйте:
```bash
sudo systemctl daemon-reload
sudo systemctl start pet-temp-monitor
sudo systemctl start pet-temp-web
sudo systemctl enable pet-temp-monitor
sudo systemctl enable pet-temp-web
```

## Логика работы приложения

### Мониторинг (temp_monitor_core.py)
1. **Чтение температуры**:
   - Выполняет `sensors` каждые `INTERVAL_SEC` секунд.
   - Парсит температуру `Core 0` (измените `get_temperature()` для других сенсоров).
2. **Логирование**:
   - Записывает в `/opt/pet_temp/logs/temp_monitor.log` в формате: `ГГГГ-ММ-ДД ЧЧ:ММ:СС,mmm - Temperature: XX.X°C`.
   - `RotatingFileHandler` (10 МБ, 5 копий).
3. **Уведомления**:
   - Температура > `THRESHOLD_TEMP` (65°C): `🚨 АЛЕРТ: Температура превысила 33°C! Текущая: XX.X°C`.
   - Температура ≤ `RECOVERY_THRESHOLD` (60°C): `✅ ВОССТАНОВЛЕНИЕ: Температура вернулась к норме. Текущая: XX.X°C`.
   - Флаг `alert_triggered` предотвращает дубли.
4. **Обработка ошибок**:
   - Логирует ошибки `sensors` или Telegram API.

### Веб-интерфейс (temp_monitor_web.py)
1. Читает логи за 7 дней.
2. График температуры (Chart.js):
   - Метки времени: `день-месяц часы:минуты` (например, `26-09 09:24`).
   - Зум (колесо, щипок), тултипы.
   - Tailwind CSS (изумрудная линия, тень).
3. Порт: 8080 (настройте `WEB_PORT`).

## Зависимости
В `/opt/pet_temp/requirements.txt`:
- `requests==2.32.3`
- `python-dateutil==2.9.0`
- `flask==3.0.3`

Стандартные библиотеки:
- `subprocess`
- `logging`
- `time`

## Планы по развитию
- Поддержка нескольких сенсоров.
- Интеграция с `shoutrrr`.
- env для передачи токена внутрь контейнера.

## Как внести вклад
Открывайте issues или pull requests на GitHub.

## Лицензия
MIT License
