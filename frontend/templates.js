/**
 * Template Library - ספריית תבניות לויזואליזציות
 * חוסך עלויות API ע"י שימוש בתבניות מוכנות במקום בניית HTML מאפס
 */

const VisualizationTemplates = {
    /**
     * גרף עמודות (Bar Chart)
     * @param {Object} config - {title, labels, data, colors}
     */
    barChart: function(config) {
        const chartId = `chart_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        return `
            <div class="visualization-card" style="margin: 2rem 0; background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3 style="margin: 0; color: #333;">${config.title || 'גרף עמודות'}</h3>
                    <div>
                        <button onclick="removeVisualization(this)" class="btn-secondary" style="padding: 0.4rem 0.8rem; font-size: 0.875rem;">
                            ❌ הסר
                        </button>
                    </div>
                </div>
                <div style="position: relative; height: 400px;">
                    <canvas id="${chartId}"></canvas>
                </div>
            </div>
            <script>
                (function() {
                    const ctx = document.getElementById('${chartId}').getContext('2d');
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: ${JSON.stringify(config.labels || [])},
                            datasets: [{
                                label: '${config.dataLabel || 'ערך'}',
                                data: ${JSON.stringify(config.data || [])},
                                backgroundColor: '${config.color || 'rgba(102, 126, 234, 0.8)'}',
                                borderColor: '${config.borderColor || 'rgba(102, 126, 234, 1)'}',
                                borderWidth: 2
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    display: false
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: {
                                        callback: function(value) {
                                            return ${config.formatValue ? 'formatCurrency(value)' : 'value'};
                                        }
                                    }
                                }
                            }
                        }
                    });
                })();
            </script>
        `;
    },

    /**
     * גרף קווים (Line Chart)
     * @param {Object} config - {title, labels, data, colors}
     */
    lineChart: function(config) {
        const chartId = `chart_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        return `
            <div class="visualization-card" style="margin: 2rem 0; background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3 style="margin: 0; color: #333;">${config.title || 'גרף קווים'}</h3>
                    <div>
                        <button onclick="removeVisualization(this)" class="btn-secondary" style="padding: 0.4rem 0.8rem; font-size: 0.875rem;">
                            ❌ הסר
                        </button>
                    </div>
                </div>
                <div style="position: relative; height: 400px;">
                    <canvas id="${chartId}"></canvas>
                </div>
            </div>
            <script>
                (function() {
                    const ctx = document.getElementById('${chartId}').getContext('2d');
                    new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: ${JSON.stringify(config.labels || [])},
                            datasets: [{
                                label: '${config.dataLabel || 'ערך'}',
                                data: ${JSON.stringify(config.data || [])},
                                borderColor: '${config.color || 'rgba(102, 126, 234, 1)'}',
                                backgroundColor: '${config.bgColor || 'rgba(102, 126, 234, 0.1)'}',
                                borderWidth: 3,
                                fill: true,
                                tension: 0.4
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    display: false
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true
                                }
                            }
                        }
                    });
                })();
            </script>
        `;
    },

    /**
     * גרף עוגה (Pie Chart)
     * @param {Object} config - {title, labels, data}
     */
    pieChart: function(config) {
        const chartId = `chart_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        const colors = [
            'rgba(102, 126, 234, 0.8)',
            'rgba(118, 75, 162, 0.8)',
            'rgba(237, 100, 166, 0.8)',
            'rgba(255, 154, 158, 0.8)',
            'rgba(255, 198, 128, 0.8)'
        ];

        return `
            <div class="visualization-card" style="margin: 2rem 0; background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3 style="margin: 0; color: #333;">${config.title || 'גרף עוגה'}</h3>
                    <div>
                        <button onclick="removeVisualization(this)" class="btn-secondary" style="padding: 0.4rem 0.8rem; font-size: 0.875rem;">
                            ❌ הסר
                        </button>
                    </div>
                </div>
                <div style="position: relative; height: 400px;">
                    <canvas id="${chartId}"></canvas>
                </div>
            </div>
            <script>
                (function() {
                    const ctx = document.getElementById('${chartId}').getContext('2d');
                    new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: ${JSON.stringify(config.labels || [])},
                            datasets: [{
                                data: ${JSON.stringify(config.data || [])},
                                backgroundColor: ${JSON.stringify(colors)},
                                borderWidth: 2,
                                borderColor: 'white'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    position: 'bottom'
                                }
                            }
                        }
                    });
                })();
            </script>
        `;
    },

    /**
     * טבלת נתונים (Data Table)
     * @param {Object} config - {title, columns, rows}
     */
    dataTable: function(config) {
        return `
            <div class="visualization-card" style="margin: 2rem 0; background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3 style="margin: 0; color: #333;">${config.title || 'טבלת נתונים'}</h3>
                    <div>
                        <button onclick="removeVisualization(this)" class="btn-secondary" style="padding: 0.4rem 0.8rem; font-size: 0.875rem;">
                            ❌ הסר
                        </button>
                    </div>
                </div>
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse; border: 2px solid #000000;">
                        <thead>
                            <tr style="background: #000000; color: #FFFFFF;">
                                ${(config.columns || []).map(col =>
                                    `<th style="padding: 12px; text-align: right; font-weight: 600; border: 2px solid #000000;">${col}</th>`
                                ).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            ${(config.rows || []).map((row, idx) => `
                                <tr>
                                    ${row.map(cell =>
                                        `<td style="padding: 12px; text-align: right; border: 2px solid #000000;">${cell}</td>`
                                    ).join('')}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    },

    /**
     * כרטיס KPI
     * @param {Object} config - {title, value, subtitle, icon}
     */
    kpiCard: function(config) {
        return `
            <div class="visualization-card" style="margin: 1rem; background: #A855F7; border: 2px solid #000000; border-radius: 8px; padding: 1.5rem; color: white; display: inline-block; min-width: 250px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <h4 style="margin: 0; font-size: 1rem; opacity: 0.9;">${config.title || 'KPI'}</h4>
                    <span style="font-size: 1.5rem;">${config.icon || '📊'}</span>
                </div>
                <div style="font-size: 2.5rem; font-weight: bold; margin: 0.5rem 0;">${config.value || '0'}</div>
                ${config.subtitle ? `<div style="opacity: 0.8; font-size: 0.875rem;">${config.subtitle}</div>` : ''}
            </div>
        `;
    }
};

// פונקציה להסרת ויזואליזציה
function removeVisualization(button) {
    const card = button.closest('.visualization-card');
    if (card) {
        card.remove();
    }
}
