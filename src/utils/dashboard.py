"""
Trading Strategy Dashboard
==========================
實時監控策略表現的 Web 儀表板

使用方法:
    python src/utils/dashboard.py

訪問:
    http://localhost:5000
"""

from flask import Flask, render_template_string, jsonify
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import os

app = Flask(__name__)

# Dashboard HTML template
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Pyxis HFT Strategy Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #1a1a1a;
            color: #e0e0e0;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            color: #4CAF50;
            text-align: center;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #2a2a2a;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #4CAF50;
        }
        .stat-label {
            color: #aaa;
            margin-top: 5px;
        }
        .charts {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .chart-container {
            background: #2a2a2a;
            padding: 20px;
            border-radius: 8px;
        }
        .status {
            text-align: center;
            padding: 10px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .status.running {
            background: #2a5a2a;
            color: #4CAF50;
        }
        .status.stopped {
            background: #5a2a2a;
            color: #ff6b6b;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Pyxis HFT Strategy Dashboard</h1>
        
        <div id="status" class="status stopped">
            Status: Checking...
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value" id="current-pnl">--</div>
                <div class="stat-label">Current PnL</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="current-position">--</div>
                <div class="stat-label">Position</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="current-mid">--</div>
                <div class="stat-label">Mid Price</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="current-spread">--</div>
                <div class="stat-label">Spread</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="current-mlofi">--</div>
                <div class="stat-label">MLOFI</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="current-volatility">--</div>
                <div class="stat-label">Volatility</div>
            </div>
        </div>
        
        <div class="charts">
            <div class="chart-container">
                <h3>PnL Over Time</h3>
                <canvas id="pnlChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>Position Over Time</h3>
                <canvas id="positionChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>MLOFI Signal</h3>
                <canvas id="mlofiChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>Spread Over Time</h3>
                <canvas id="spreadChart"></canvas>
            </div>
        </div>
    </div>
    
    <script>
        // Initialize charts
        const pnlCtx = document.getElementById('pnlChart').getContext('2d');
        const positionCtx = document.getElementById('positionChart').getContext('2d');
        const mlofiCtx = document.getElementById('mlofiChart').getContext('2d');
        const spreadCtx = document.getElementById('spreadChart').getContext('2d');
        
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: { ticks: { color: '#aaa' }, grid: { color: '#333' } },
                y: { ticks: { color: '#aaa' }, grid: { color: '#333' } }
            },
            plugins: {
                legend: { labels: { color: '#aaa' } }
            }
        };
        
        const pnlChart = new Chart(pnlCtx, {
            type: 'line',
            data: { labels: [], datasets: [{ label: 'PnL', data: [], borderColor: '#4CAF50', backgroundColor: 'rgba(76, 175, 80, 0.1)' }] },
            options: chartOptions
        });
        
        const positionChart = new Chart(positionCtx, {
            type: 'line',
            data: { labels: [], datasets: [{ label: 'Position', data: [], borderColor: '#2196F3', backgroundColor: 'rgba(33, 150, 243, 0.1)' }] },
            options: chartOptions
        });
        
        const mlofiChart = new Chart(mlofiCtx, {
            type: 'line',
            data: { labels: [], datasets: [{ label: 'MLOFI', data: [], borderColor: '#FF9800', backgroundColor: 'rgba(255, 152, 0, 0.1)' }] },
            options: chartOptions
        });
        
        const spreadChart = new Chart(spreadCtx, {
            type: 'line',
            data: { labels: [], datasets: [{ label: 'Spread', data: [], borderColor: '#9C27B0', backgroundColor: 'rgba(156, 39, 176, 0.1)' }] },
            options: chartOptions
        });
        
        // Update dashboard
        function updateDashboard() {
            fetch('/api/data')
                .then(response => response.json())
                .then(data => {
                    // Update status
                    const statusEl = document.getElementById('status');
                    if (data.status === 'running') {
                        statusEl.className = 'status running';
                        statusEl.textContent = '[RUNNING] Strategy Running';
                    } else {
                        statusEl.className = 'status stopped';
                        statusEl.textContent = '[STOPPED] Strategy Stopped';
                    }
                    
                    // Update stats
                    if (data.latest) {
                        document.getElementById('current-pnl').textContent = data.latest.pnl.toFixed(2);
                        document.getElementById('current-position').textContent = data.latest.position.toFixed(4);
                        document.getElementById('current-mid').textContent = data.latest.mid_price.toFixed(1);
                        document.getElementById('current-spread').textContent = data.latest.spread.toFixed(2);
                        document.getElementById('current-mlofi').textContent = data.latest.mlofi.toFixed(3);
                        document.getElementById('current-volatility').textContent = data.latest.volatility.toFixed(2);
                    }
                    
                    // Update charts
                    if (data.history && data.history.length > 0) {
                        const labels = data.history.map(d => new Date(d.timestamp).toLocaleTimeString());
                        
                        pnlChart.data.labels = labels;
                        pnlChart.data.datasets[0].data = data.history.map(d => d.pnl);
                        pnlChart.update('none');
                        
                        positionChart.data.labels = labels;
                        positionChart.data.datasets[0].data = data.history.map(d => d.position);
                        positionChart.update('none');
                        
                        mlofiChart.data.labels = labels;
                        mlofiChart.data.datasets[0].data = data.history.map(d => d.mlofi);
                        mlofiChart.update('none');
                        
                        spreadChart.data.labels = labels;
                        spreadChart.data.datasets[0].data = data.history.map(d => d.spread);
                        spreadChart.update('none');
                    }
                })
                .catch(error => console.error('Error:', error));
        }
        
        // Update every 2 seconds
        setInterval(updateDashboard, 2000);
        updateDashboard();
    </script>
</body>
</html>
"""


def get_latest_log_file():
    """獲取最新的日誌文件"""
    log_dir = Path('logs/trading')
    if not log_dir.exists():
        return None
    
    csv_files = list(log_dir.glob('performance_*.csv'))
    if not csv_files:
        return None
    
    # 返回最新的文件
    return max(csv_files, key=lambda p: p.stat().st_mtime)


@app.route('/')
def dashboard():
    """顯示儀表板"""
    return render_template_string(DASHBOARD_TEMPLATE)


@app.route('/api/data')
def get_data():
    """獲取策略數據 API"""
    log_file = get_latest_log_file()
    
    if not log_file or not log_file.exists():
        return jsonify({
            'status': 'stopped',
            'latest': None,
            'history': []
        })
    
    try:
        # 讀取 CSV 數據
        df = pd.read_csv(log_file)
        
        if len(df) == 0:
            return jsonify({
                'status': 'stopped',
                'latest': None,
                'history': []
            })
        
        # 檢查文件是否最近更新（5分鐘內認為在運行）
        file_mtime = log_file.stat().st_mtime
        time_diff = datetime.now().timestamp() - file_mtime
        status = 'running' if time_diff < 300 else 'stopped'  # 5分鐘
        
        # 獲取最新數據
        latest = df.iloc[-1].to_dict()
        
        # 獲取歷史數據（最近100條）
        history = df.tail(100).to_dict('records')
        
        # 計算 spread
        if 'spread' not in latest:
            latest['spread'] = latest.get('ask_price', 0) - latest.get('bid_price', 0)
        
        return jsonify({
            'status': status,
            'latest': {
                'pnl': latest.get('pnl', 0),
                'position': latest.get('position', 0),
                'mid_price': latest.get('mid_price', 0),
                'spread': latest.get('spread', 0),
                'mlofi': latest.get('mlofi', 0),
                'volatility': latest.get('volatility', 0),
            },
            'history': history
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'latest': None,
            'history': []
        })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Pyxis HFT Strategy Dashboard")
    print("="*60)
    print("Access dashboard at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)

