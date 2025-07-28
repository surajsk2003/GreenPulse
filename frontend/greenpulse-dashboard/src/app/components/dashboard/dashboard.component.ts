import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatSelectModule } from '@angular/material/select';
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatIconModule } from '@angular/material/icon';
import { EnergyService, Building, Insight, Anomaly } from '../../services/energy.service';
import { EnergyChartComponent } from '../energy-chart/energy-chart.component';
import { InsightsPanelComponent } from '../insights-panel/insights-panel.component';
import { LeaderboardComponent } from '../leaderboard/leaderboard.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatSelectModule,
    MatCardModule,
    MatProgressBarModule,
    MatIconModule,
    EnergyChartComponent,
    InsightsPanelComponent,
    LeaderboardComponent
  ],
  template: `
    <div class="dashboard-container">
      <!-- Header -->
      <header class="dashboard-header">
        <div class="header-top">
          <h1>🌱 GreenPulse Dashboard</h1>
          <div class="connection-status" [class.connected]="isConnected" [class.disconnected]="!isConnected">
            <div class="status-indicator"></div>
            <span class="status-text">{{isConnected ? 'Live' : 'Offline'}}</span>
            <small class="last-update" *ngIf="isConnected">Updated {{lastUpdate | date:'HH:mm:ss'}}</small>
          </div>
        </div>
        <div class="campus-stats">
          <div class="stat-card">
            <span class="stat-value">{{totalEnergy | number:'1.0-1'}} kWh</span>
            <span class="stat-label">Current Usage</span>
          </div>
          <div class="stat-card">
            <span class="stat-value">{{efficiencyScore}}</span>
            <span class="stat-label">Efficiency Score</span>
          </div>
          <div class="stat-card alert" *ngIf="activeAlerts > 0">
            <span class="stat-value">{{activeAlerts}}</span>
            <span class="stat-label">Active Alerts</span>
          </div>
          <div class="stat-card success">
            <span class="stat-value">\${{estimatedSavings | number:'1.0-0'}}</span>
            <span class="stat-label">Potential Savings</span>
          </div>
        </div>
      </header>

      <!-- Main Content -->
      <div class="dashboard-content">
        <!-- Building Selector -->
        <div class="controls-section">
          <mat-select 
            [(value)]="selectedBuilding" 
            (selectionChange)="onBuildingChange($event)"
            placeholder="Select Building"
            class="building-selector">
            <mat-option *ngFor="let building of buildings" [value]="building.id">
              {{building.name}} ({{building.building_type}})
            </mat-option>
          </mat-select>
          
          <div class="time-controls">
            <button 
              *ngFor="let period of timePeriods" 
              [class.active]="period.value === selectedPeriod"
              (click)="changePeriod(period.value)"
              class="time-btn">
              {{period.label}}
            </button>
          </div>
        </div>

        <!-- Charts Grid -->
        <div class="charts-grid" *ngIf="selectedBuilding">
          <div class="chart-panel main-chart">
            <app-energy-chart 
              [energyData]="currentEnergyData"
              [anomalies]="anomalies"
              [forecast]="forecast"
              [loading]="loadingChart">
            </app-energy-chart>
          </div>
          
          <div class="insights-panel">
            <app-insights-panel 
              [insights]="aiInsights"
              [loading]="loadingInsights">
            </app-insights-panel>
          </div>

          <div class="leaderboard-panel">
            <app-leaderboard 
              [leaderboard]="leaderboard"
              [loading]="loadingLeaderboard">
            </app-leaderboard>
          </div>

          <!-- Building Details Card -->
          <div class="building-details-card">
            <mat-card>
              <mat-card-header>
                <mat-card-title>Building Details</mat-card-title>
              </mat-card-header>
              <mat-card-content *ngIf="selectedBuildingDetails">
                <div class="detail-row">
                  <span class="label">Type:</span>
                  <span class="value">{{selectedBuildingDetails.building_type}}</span>
                </div>
                <div class="detail-row">
                  <span class="label">Area:</span>
                  <span class="value">{{selectedBuildingDetails.area_sqft | number}} sq ft</span>
                </div>
                <div class="detail-row">
                  <span class="label">Year Built:</span>
                  <span class="value">{{selectedBuildingDetails.year_built}}</span>
                </div>
                <div class="detail-row">
                  <span class="label">Efficiency:</span>
                  <span class="value">{{selectedBuildingDetails.efficiency_score}}%</span>
                  <mat-progress-bar 
                    [value]="selectedBuildingDetails.efficiency_score" 
                    [color]="getEfficiencyColor(selectedBuildingDetails.efficiency_score)">
                  </mat-progress-bar>
                </div>
                <div class="detail-row">
                  <span class="label">Current Usage:</span>
                  <span class="value">{{selectedBuildingDetails.current_usage | number:'1.2-2'}} kWh</span>
                </div>
              </mat-card-content>
            </mat-card>
          </div>
        </div>

        <!-- Loading State -->
        <div class="loading-state" *ngIf="!selectedBuilding && !loadingBuildings">
          <mat-icon>business</mat-icon>
          <h3>Select a building to view energy data</h3>
          <p>Choose from {{buildings.length}} available buildings to start monitoring energy consumption</p>
        </div>

        <!-- Error State -->
        <div class="error-state" *ngIf="errorMessage">
          <mat-icon>error</mat-icon>
          <h3>Unable to load data</h3>
          <p>{{errorMessage}}</p>
          <button (click)="retryLoad()" class="retry-btn">Retry</button>
        </div>
      </div>
    </div>
  `,
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  buildings: Building[] = [];
  selectedBuilding: number = 0;
  selectedBuildingDetails: Building | null = null;
  currentEnergyData: any[] = [];
  anomalies: Anomaly[] = [];
  forecast: any[] = [];
  aiInsights: Insight[] = [];
  leaderboard: any[] = [];
  
  // Stats
  totalEnergy: number = 0;
  efficiencyScore: number = 75;
  activeAlerts: number = 0;
  estimatedSavings: number = 0;
  
  // Time periods
  selectedPeriod: number = 24;
  timePeriods = [
    { label: '24H', value: 24 },
    { label: '7D', value: 168 },
    { label: '30D', value: 720 }
  ];
  
  // Loading states
  loadingBuildings: boolean = true;
  loadingChart: boolean = false;
  loadingInsights: boolean = false;
  loadingLeaderboard: boolean = false;
  
  // Real-time connection status
  isConnected: boolean = false;
  lastUpdate: Date = new Date();
  
  errorMessage: string = '';

  constructor(private energyService: EnergyService) {}

  ngOnInit() {
    this.loadBuildings();
    this.loadCampusStats();
    this.loadLeaderboard();
    
    // Subscribe to WebSocket connection status
    this.energyService.wsConnection$.subscribe(connected => {
      this.isConnected = connected;
    });
    
    // Subscribe to real-time data updates
    this.energyService.realTimeData$.subscribe(data => {
      if (data.length > 0) {
        this.lastUpdate = new Date();
        // Update current energy data with real-time readings
        if (this.currentEnergyData.length > 0) {
          this.currentEnergyData = [...this.currentEnergyData.slice(0, -data.length), ...data];
        }
      }
    });
    
    // Set up periodic updates (fallback if WebSocket fails)
    setInterval(() => {
      this.loadCampusStats();
      if (this.selectedBuilding && !this.isConnected) {
        this.loadBuildingData();
      }
    }, 60000); // Update every minute
  }

  loadBuildings() {
    this.loadingBuildings = true;
    this.energyService.getBuildings().subscribe({
      next: (buildings) => {
        this.buildings = buildings;
        this.loadingBuildings = false;
        
        if (buildings.length > 0) {
          this.selectedBuilding = buildings[0].id;
          this.onBuildingChange({ value: this.selectedBuilding });
        }
      },
      error: (error) => {
        this.errorMessage = 'Failed to load buildings. Please check if the backend is running.';
        this.loadingBuildings = false;
        console.error('Error loading buildings:', error);
      }
    });
  }

  loadCampusStats() {
    this.energyService.getCampusStats().subscribe({
      next: (stats) => {
        this.totalEnergy = stats.overview?.total_usage_24h || 0;
        this.efficiencyScore = 75; // Mock value
        this.activeAlerts = stats.alerts?.active_anomalies || 0;
      },
      error: (error) => {
        console.error('Error loading campus stats:', error);
      }
    });
  }

  loadLeaderboard() {
    this.loadingLeaderboard = true;
    this.energyService.getEfficiencyLeaderboardML().subscribe({
      next: (data) => {
        this.leaderboard = data.leaderboard || [];
        this.loadingLeaderboard = false;
      },
      error: (error) => {
        console.error('Error loading ML leaderboard:', error);
        // Fallback to regular leaderboard
        this.energyService.getEfficiencyLeaderboard('week').subscribe({
          next: (fallbackData) => {
            this.leaderboard = fallbackData.leaderboard || [];
            this.loadingLeaderboard = false;
          },
          error: (fallbackError) => {
            console.error('Error loading fallback leaderboard:', fallbackError);
            this.loadingLeaderboard = false;
          }
        });
      }
    });
  }

  onBuildingChange(event: any) {
    let buildingId: number;
    
    // Handle different event types
    if (typeof event === 'number') {
      buildingId = event;
    } else if (event && typeof event.value === 'number') {
      buildingId = event.value;
    } else if (event && event.value) {
      buildingId = parseInt(event.value, 10);
    } else if (typeof event === 'string') {
      buildingId = parseInt(event, 10);
    } else {
      console.error('Invalid building ID received:', event);
      return;
    }
    
    if (isNaN(buildingId)) {
      console.error('Building ID is not a valid number:', event);
      return;
    }
    
    this.selectedBuilding = buildingId;
    this.selectedBuildingDetails = this.buildings.find(b => b.id === buildingId) || null;
    this.energyService.setSelectedBuilding(buildingId);
    this.loadBuildingData();
  }

  loadBuildingData() {
    if (!this.selectedBuilding) return;

    this.loadingChart = true;
    this.loadingInsights = true;

    // Load energy data
    this.energyService.getHistoricalEnergy(this.selectedBuilding, this.selectedPeriod).subscribe({
      next: (data) => {
        this.currentEnergyData = data.readings || [];
        this.loadingChart = false;
      },
      error: (error) => {
        console.error('Error loading energy data:', error);
        this.loadingChart = false;
      }
    });

    // Load ML anomalies
    this.energyService.detectAnomalies(this.selectedBuilding, 24).subscribe({
      next: (data) => {
        this.anomalies = data.anomalies || [];
        this.activeAlerts = data.anomaly_count || 0;
      },
      error: (error) => {
        console.error('Error loading ML anomalies:', error);
        // Fallback to regular anomalies
        this.energyService.getBuildingAnomalies(this.selectedBuilding).subscribe({
          next: (fallbackData) => {
            this.anomalies = fallbackData.anomalies || [];
            this.activeAlerts = fallbackData.anomaly_count || 0;
          },
          error: (fallbackError) => {
            console.error('Error loading fallback anomalies:', fallbackError);
          }
        });
      }
    });

    // Load ML forecast
    this.energyService.getEnergyForecastML(this.selectedBuilding, 24).subscribe({
      next: (data) => {
        this.forecast = data.forecast || [];
      },
      error: (error) => {
        console.error('Error loading ML forecast:', error);
        // Fallback to regular forecast
        this.energyService.getEnergyForecast(this.selectedBuilding, 24).subscribe({
          next: (fallbackData) => {
            this.forecast = fallbackData.forecast || [];
          },
          error: (fallbackError) => {
            console.error('Error loading fallback forecast:', fallbackError);
          }
        });
      }
    });

    // Load AI insights
    this.energyService.getAIInsights(this.selectedBuilding, 7).subscribe({
      next: (data) => {
        // Convert AI insights to match the expected format
        const insights = (data.insights || []).map((insight: string, index: number) => ({
          id: `ai-${index}`,
          type: 'ai_generated',
          priority: 1,
          title: 'AI Insight',
          description: insight,
          recommendation: data.recommendations?.[index] || 'No specific recommendation',
          potential_savings_usd: Math.random() * 1000, // Mock savings
          actionable_steps: data.recommendations || [],
          category: 'energy_efficiency',
          impact: 'medium'
        }));
        
        this.aiInsights = insights;
        this.estimatedSavings = insights.reduce((total: number, insight: any) => 
          total + (insight.potential_savings_usd || 0), 0);
        this.loadingInsights = false;
      },
      error: (error) => {
        console.error('Error loading AI insights:', error);
        // Fallback to regular insights
        this.energyService.getBuildingInsights(this.selectedBuilding).subscribe({
          next: (fallbackData) => {
            this.aiInsights = fallbackData.insights || [];
            this.estimatedSavings = this.aiInsights.reduce((total, insight) => 
              total + (insight.potential_savings_usd || 0), 0);
            this.loadingInsights = false;
          },
          error: (fallbackError) => {
            console.error('Error loading fallback insights:', fallbackError);
            this.loadingInsights = false;
          }
        });
      }
    });
  }

  changePeriod(period: number) {
    this.selectedPeriod = period;
    if (this.selectedBuilding) {
      this.loadBuildingData();
    }
  }

  getEfficiencyColor(score: number): string {
    if (score >= 80) return 'primary';
    if (score >= 60) return 'accent';
    return 'warn';
  }

  retryLoad() {
    this.errorMessage = '';
    this.loadBuildings();
  }
}