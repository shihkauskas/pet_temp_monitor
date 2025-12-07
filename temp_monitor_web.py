from flask import Flask, render_template_string, jsonify
from dateutil.parser import parse as parse_date
import datetime
import os
import subprocess
import re

# Конфигурация
LOG_FILE = '/opt/pet_temp/logs/temp_monitor.log'
BACKUP_COUNT = 5
WEB_PORT = 8080

app = Flask(__name__)

def read_logs_last_7_days():
    logs = []
    seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    files_to_read = [LOG_FILE] + [
        f"{LOG_FILE}.{i}" for i in range(1, BACKUP_COUNT + 1)
        if os.path.exists(f"{LOG_FILE}.{i}")
    ]
    for file in files_to_read:
        if os.path.exists(file):
            with open(file, 'r') as f:
                for line in f:
                    try:
                        timestamp_str, message = line.strip().split(' - ', 1)
                        if 'Temperature:' in message:
                            temp = float(message.split(': ')[1].split('°')[0])
                            timestamp = parse_date(timestamp_str)
                            if timestamp >= seven_days_ago:
                                logs.append({
                                    'timestamp': timestamp.strftime('%d-%m %H:%M'),
                                    'temp': temp
                                })
                    except Exception:
                        pass
    # Сортировка по времени (по возрастанию)
    return sorted(
        logs,
        key=lambda x: datetime.datetime.strptime(x['timestamp'], '%d-%m %H:%M')
    )

def get_current_temp():
    try:
        result = subprocess.run(['sensors'], capture_output=True, text=True, timeout=3)
        if result.returncode != 0:
            return None
        # Ищем первую подходящую строку с температурой
        for line in result.stdout.splitlines():
            match = re.search(r'\+?(\d+\.\d+)[°\s]*C', line)
            if match:
                return float(match.group(1))
        return None
    except Exception:
        return None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Монитор температуры</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.0.1"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 font-sans">
    <div class="container mx-auto p-6">
        <h1 class="text-3xl font-bold text-gray-800 mb-8 text-center">Монитор температуры (последние 7 дней)</h1>
        <div class="bg-white p-8 rounded-lg shadow-lg mb-6">
            <canvas id="tempChart" class="w-full h-[500px]"></canvas>
        </div>
        <div id="current-temp" class="text-center text-lg font-semibold text-gray-700">
            Текущая температура: <span id="temp-value">–</span> °C
        </div>
    </div>

    <script>
        Chart.register({
            id: 'dropshadow',
            beforeDraw: function(chart) {
                const ctx = chart.ctx;
                ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
                ctx.shadowBlur = 8;
                ctx.shadowOffsetX = 2;
                ctx.shadowOffsetY = 2;
            }
        });

        // Загрузка исторических данных (7 дней)
        fetch('/data')
            .then(response => response.json())
            .then(data => {
                const ctx = document.getElementById('tempChart').getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.map(d => d.timestamp),
                        datasets: [{
                            label: 'Температура (°C)',
                            data: data.map(d => d.temp),
                            borderColor: '#10B981',
                            backgroundColor: 'rgba(16, 185, 129, 0.2)',
                            fill: true,
                            tension: 0.4,
                            pointRadius: 0,
                            pointHoverRadius: 0
                        }]
                    },
                    options: {
                        plugins: {
                            tooltip: {
                                enabled: true,
                                mode: 'nearest',
                                intersect: false,
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                titleFont: { family: 'Arial', size: 14, weight: 'bold' },
                                bodyFont: { family: 'Arial', size: 12 },
                                padding: 10,
                                callbacks: {
                                    label: context => `Температура: ${context.parsed.y}°C`,
                                    title: context => context[0].label
                                }
                            },
                            zoom: {
                                zoom: {
                                    wheel: { enabled: true },
                                    pinch: { enabled: true },
                                    mode: 'xy'
                                },
                                pan: {
                                    enabled: true,
                                    mode: 'xy'
                                }
                            }
                        },
                        scales: {
                            x: {
                                title: { 
                                    display: true, 
                                    text: 'Время (день-месяц часы:минуты)', 
                                    font: { family: 'Arial', size: 14, weight: 'bold' },
                                    color: '#1F2937'
                                },
                                grid: { display: false },
                                ticks: { font: { family: 'Arial', size: 12 }, color: '#1F2937' }
                            },
                            y: {
                                title: { 
                                    display: true, 
                                    text: 'Температура (°C)', 
                                    font: { family: 'Arial', size: 14, weight: 'bold' },
                                    color: '#1F2937'
                                },
                                grid: { color: '#E5E7EB' },
                                ticks: { font: { family: 'Arial', size: 12 }, color: '#1F2937' },
                                beginAtZero: false
                            }
                        },
                        animation: {
                            duration: 1000,
                            easing: 'easeInOutQuad'
                        },
                        maintainAspectRatio: false
                    }
                });
            });

        // Обновление текущей температуры каждые 5 секунд
        function updateCurrentTemp() {
            fetch('/current_temp')
                .then(response => response.json())
                .then(data => {
                    const el = document.getElementById('temp-value');
                    if (data.temp !== null) {
                        el.textContent = data.temp.toFixed(1);
                        el.parentElement.classList.remove('text-gray-500');
                    } else {
                        el.textContent = '–';
                        el.parentElement.classList.add('text-gray-500');
                    }
                })
                .catch(() => {
                    document.getElementById('temp-value').textContent = 'ошибка';
                });
        }

        updateCurrentTemp();
        setInterval(updateCurrentTemp, 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/data')
def data():
    logs = read_logs_last_7_days()
    return jsonify(logs)

@app.route('/current_temp')
def current_temp():
    temp = get_current_temp()
    return jsonify({'temp': temp})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=WEB_PORT)
