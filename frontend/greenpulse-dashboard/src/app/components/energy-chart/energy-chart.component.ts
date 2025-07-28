import { Component, Input, OnInit, OnChanges, ViewChild, ElementRef, SimpleChanges, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Chart, ChartConfiguration, ChartType, registerables, TimeUnit } from 'chart.js';
import 'chartjs-adapter-date-fns';

Chart.register(...registerables);

@Component({
  selector: 'app-energy-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="chart-container">
      <div class="chart-header">
        <h3>⚡ Energy Consumption</h3>
        <div class="chart-controls">
          <button 
            *ngFor="let type of chartTypes" 
            [class.active]="type.value === selectedChartType"
            (click)="changeChartType(type.value)"
            class="chart-type-btn">
            {{type.label}}
          </button>
        </div>
      </div>
      
      <div class="chart-content" [class.loading]="loading">
        <canvas #chartCanvas></canvas>
        
        <!-- Loading overlay -->
        <div class="loading-overlay" *ngIf="loading">
          <div class="spinner"></div>
          <span>Loading energy data...</span>
        </div>
        
        <!-- No data message -->
        <div class="no-data-message" *ngIf="!loading && (!energyData || energyData.length === 0)">
          <span>📊 No energy data available</span>
          <p>Select a building to view energy consumption patterns</p>
        </div>
      </div>
      
      <!-- Chart Legend -->
      <div class="chart-legend" *ngIf="!loading && energyData && energyData.length > 0">
        <div class="legend-item">
          <div class="legend-color" style="background: #4facfe;"></div>
          <span>Current Usage</span>
        </div>
        <div class="legend-item" *ngIf="forecast && forecast.length > 0">
          <div class="legend-color" style="background: #ff9500;"></div>
          <span>Forecast</span>
        </div>
        <div class="legend-item" *ngIf="anomalies && anomalies.length > 0">
          <div class="legend-color" style="background: #ff6b6b;"></div>
          <span>Anomalies ({{anomalies.length}})</span>
        </div>
      </div>
    </div>
  `,
  styleUrls: ['./energy-chart.component.scss']
})
export class EnergyChartComponent implements OnInit, OnChanges, OnDestroy {
  @Input() energyData: any[] = [];
  @Input() anomalies: any[] = [];
  @Input() forecast: any[] = [];
  @Input() loading: boolean = false;
  
  @ViewChild('chartCanvas', { static: true }) chartCanvas!: ElementRef<HTMLCanvasElement>;
  
  private chart: Chart | null = null;
  
  selectedChartType: string = 'line';
  chartTypes = [
    { label: 'Line', value: 'line' },
    { label: 'Bar', value: 'bar' },
    { label: 'Area', value: 'area' }
  ];

  ngOnInit() {
    // Add a small delay to ensure DOM is fully ready
    setTimeout(() => {
      this.initializeChart();
    }, 100);
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['energyData'] || changes['forecast'] || changes['anomalies']) {
      this.updateChart();
    }
  }

  initializeChart() {
    // Destroy existing chart if it exists
    if (this.chart) {
      this.chart.destroy();
      this.chart = null;
    }

    const ctx = this.chartCanvas.nativeElement.getContext('2d');
    if (!ctx) return;

    // Clear any existing Chart.js instance on this canvas
    const existingChart = Chart.getChart(ctx);
    if (existingChart) {
      existingChart.destroy();
    }

    this.chart = new Chart(ctx, this.getChartConfig());
  }

  updateChart() {
    // If chart doesn't exist or canvas is not ready, initialize
    if (!this.chart || !this.chartCanvas?.nativeElement) {
      if (this.chartCanvas?.nativeElement) {
        this.initializeChart();
      }
      return;
    }

    try {
      const config = this.getChartConfig();
      
      // Destroy and recreate chart if type changed
      if ((this.chart.config as any).type !== config.type) {
        this.chart.destroy();
        this.chart = null;
        this.initializeChart();
        return;
      }
      
      this.chart.data = config.data;
      this.chart.options = config.options!;
      this.chart.update('active');
    } catch (error) {
      console.warn('Chart update failed, reinitializing:', error);
      this.initializeChart();
    }
  }

  getChartConfig(): ChartConfiguration {
    const datasets = [];
    
    // Main energy data
    if (this.energyData && this.energyData.length > 0) {
      const energyDataset: any = {
        label: 'Energy Usage (kWh)',
        data: this.energyData.map(d => ({
          x: new Date(d.timestamp),
          y: d.meter_reading || 0
        })),
        borderColor: '#4facfe',
        backgroundColor: this.selectedChartType === 'area' ? 'rgba(79, 172, 254, 0.3)' : 
                         this.selectedChartType === 'bar' ? 'rgba(79, 172, 254, 0.6)' : 'rgba(79, 172, 254, 0.1)',
        fill: this.selectedChartType === 'area',
        tension: this.selectedChartType === 'bar' ? 0 : 0.4,
        pointRadius: this.selectedChartType === 'bar' ? 0 : 2,
        pointHoverRadius: this.selectedChartType === 'bar' ? 0 : 6,
        barThickness: this.selectedChartType === 'bar' ? 'flex' : undefined,
        maxBarThickness: this.selectedChartType === 'bar' ? 20 : undefined
      };
      datasets.push(energyDataset);
    }

    // Forecast data
    if (this.forecast && this.forecast.length > 0) {
      const forecastDataset: any = {
        label: 'Forecast',
        data: this.forecast.map(f => ({
          x: new Date(f.timestamp),
          y: f.predicted_usage || f.predicted_kwh || 0
        })),
        borderColor: '#ff9500',
        backgroundColor: this.selectedChartType === 'bar' ? 'rgba(255, 149, 0, 0.6)' : 'rgba(255, 149, 0, 0.1)',
        borderDash: this.selectedChartType === 'bar' ? [] : [5, 5],
        fill: false,
        tension: this.selectedChartType === 'bar' ? 0 : 0.4,
        pointRadius: this.selectedChartType === 'bar' ? 0 : 2,
        barThickness: this.selectedChartType === 'bar' ? 'flex' : undefined,
        maxBarThickness: this.selectedChartType === 'bar' ? 15 : undefined
      };
      datasets.push(forecastDataset);
      
      // Confidence interval
      if (this.forecast[0]?.confidence_lower !== undefined) {
        const confidenceDataset = {
          label: 'Confidence Interval',
          data: this.forecast.map(f => ({
            x: new Date(f.timestamp),
            y: [f.confidence_lower, f.confidence_upper]
          })),
          backgroundColor: 'rgba(255, 149, 0, 0.1)',
          borderColor: 'transparent',
          fill: true
        };
        datasets.push(confidenceDataset);
      }
    }

    // Anomaly points
    if (this.anomalies && this.anomalies.length > 0) {
      const anomalyDataset = {
        label: 'Anomalies',
        data: this.anomalies.map(a => ({
          x: new Date(a.timestamp),
          y: a.energy_value
        })),
        backgroundColor: '#ff6b6b',
        borderColor: '#ff6b6b',
        pointRadius: 8,
        pointHoverRadius: 10,
        showLine: false,
        pointStyle: 'triangle'
      };
      datasets.push(anomalyDataset);
    }

    return {
      type: (this.selectedChartType === 'area' ? 'line' : this.selectedChartType) as ChartType,
      data: { datasets: datasets as any },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: false
          },
          legend: {
            display: false // We have custom legend
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
              label: (context) => {
                const label = context.dataset.label || '';
                const value = typeof context.parsed.y === 'number' 
                  ? context.parsed.y.toFixed(2) 
                  : context.parsed.y;
                return `${label}: ${value} kWh`;
              }
            }
          }
        },
        scales: {
          x: {
            type: 'time',
            time: {
              unit: this.getTimeUnit(),
              displayFormats: {
                hour: 'MMM dd HH:mm',
                day: 'MMM dd',
                week: 'MMM dd'
              }
            },
            title: {
              display: true,
              text: 'Time'
            },
            grid: {
              color: 'rgba(0,0,0,0.1)'
            }
          },
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Energy (kWh)'
            },
            grid: {
              color: 'rgba(0,0,0,0.1)'
            }
          }
        },
        interaction: {
          mode: 'nearest',
          axis: 'x',
          intersect: false
        },
        animation: {
          duration: 750,
          easing: 'easeInOutQuart'
        }
      }
    };
  }

  getTimeUnit(): TimeUnit {
    if (!this.energyData || this.energyData.length < 2) return 'hour';
    
    const firstTime = new Date(this.energyData[0].timestamp);
    const lastTime = new Date(this.energyData[this.energyData.length - 1].timestamp);
    const diffHours = (lastTime.getTime() - firstTime.getTime()) / (1000 * 60 * 60);
    
    if (diffHours <= 48) return 'hour';
    if (diffHours <= 168) return 'day'; // 7 days
    return 'day';
  }

  changeChartType(type: string) {
    if (this.selectedChartType === type) return;
    
    this.selectedChartType = type;
    
    // Force chart recreation for type changes
    try {
      if (this.chart) {
        this.chart.destroy();
        this.chart = null;
      }
      
      // Small delay to ensure cleanup is complete
      setTimeout(() => {
        this.initializeChart();
      }, 50);
    } catch (error) {
      console.warn('Chart type change failed:', error);
      this.initializeChart();
    }
  }

  ngOnDestroy() {
    try {
      if (this.chart) {
        this.chart.destroy();
        this.chart = null;
      }
      
      // Also clear any Chart.js instance on the canvas
      if (this.chartCanvas?.nativeElement) {
        const ctx = this.chartCanvas.nativeElement.getContext('2d');
        if (ctx) {
          const existingChart = Chart.getChart(ctx);
          if (existingChart) {
            existingChart.destroy();
          }
        }
      }
    } catch (error) {
      console.warn('Chart cleanup failed:', error);
    }
  }
}