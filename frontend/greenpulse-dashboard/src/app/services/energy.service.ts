import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { BehaviorSubject, Observable, timer, Subject } from 'rxjs';
import { map, shareReplay, switchMap, catchError } from 'rxjs/operators';
import { of } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Building {
  id: number;
  name: string;
  building_type: string;
  primary_use: string;
  area_sqft: number;
  year_built: number;
  current_usage: number;
  efficiency_score: number;
}

export interface EnergyReading {
  timestamp: string;
  meter_reading: number;
  meter_type: number;
  air_temperature?: number;
}

export interface EnergyData {
  building_id: number;
  readings: EnergyReading[];
  summary: {
    total_readings: number;
    avg_usage: number;
    max_usage: number;
    min_usage: number;
  };
}

export interface Anomaly {
  id: string;
  timestamp: string;
  anomaly_score: number;
  anomaly_type: string;
  energy_value: number;
  severity: string;
  description?: string;
}

export interface Insight {
  id: string;
  type: string;
  priority: number;
  title: string;
  description: string;
  recommendation: string;
  potential_savings_usd: number;
  actionable_steps: string[];
  category: string;
  impact: string;
}

@Injectable({
  providedIn: 'root'
})
export class EnergyService {
  private readonly apiUrl = environment.apiUrl;
  private readonly wsUrl = environment.apiUrl.replace('http', 'ws') + '/ws';
  private selectedBuildingSubject = new BehaviorSubject<number>(0);
  private realTimeDataSubject = new BehaviorSubject<EnergyReading[]>([]);
  private websocket?: WebSocket;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private wsConnectionSubject = new Subject<boolean>();

  public selectedBuilding$ = this.selectedBuildingSubject.asObservable();
  public realTimeData$ = this.realTimeDataSubject.asObservable();
  public wsConnection$ = this.wsConnectionSubject.asObservable();

  constructor(private http: HttpClient) {
    this.startRealTimeUpdates();
    this.initWebSocket();
  }

  private startRealTimeUpdates() {
    // Update every 30 seconds
    timer(0, 30000).pipe(
      switchMap(() => this.selectedBuilding$),
      switchMap(buildingId => {
        if (buildingId === 0) return of(null);
        return this.getCurrentEnergy(buildingId).pipe(
          catchError(() => of(null))
        );
      })
    ).subscribe(data => {
      if (data) {
        const currentData = this.realTimeDataSubject.value;
        const newReading: EnergyReading = {
          timestamp: data.timestamp,
          meter_reading: data.meter_reading,
          meter_type: data.meter_type,
          air_temperature: data.air_temperature
        };
        const updatedData = [...currentData.slice(-23), newReading];
        this.realTimeDataSubject.next(updatedData);
      }
    });
  }

  setSelectedBuilding(buildingId: number) {
    this.selectedBuildingSubject.next(buildingId);
  }

  getBuildings(): Observable<Building[]> {
    return this.http.get<Building[]>(`${this.apiUrl}/buildings`).pipe(
      shareReplay(1),
      catchError(error => {
        console.error('Error fetching buildings:', error);
        return of([]);
      })
    );
  }

  getCurrentEnergy(buildingId: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/energy/buildings/${buildingId}/current`);
  }

  getHistoricalEnergy(buildingId: number, hours: number = 24): Observable<EnergyData> {
    const params = new HttpParams().set('hours', hours.toString());
    return this.http.get<EnergyData>(`${this.apiUrl}/energy/buildings/${buildingId}/historical`, { params });
  }

  getBuildingAnomalies(buildingId: number): Observable<{ anomalies: Anomaly[], anomaly_count: number }> {
    return this.http.get<{ anomalies: Anomaly[], anomaly_count: number }>
      (`${this.apiUrl}/analytics/buildings/${buildingId}/anomalies`);
  }

  getEnergyForecast(buildingId: number, hours: number = 24): Observable<any> {
    const params = new HttpParams().set('hours', hours.toString());
    return this.http.get(`${this.apiUrl}/analytics/buildings/${buildingId}/forecast`, { params });
  }

  getBuildingInsights(buildingId: number): Observable<{ insights: Insight[] }> {
    return this.http.get<{ insights: Insight[] }>(`${this.apiUrl}/insights/buildings/${buildingId}`);
  }

  getEfficiencyLeaderboard(period: string = 'week'): Observable<any> {
    const params = new HttpParams().set('period', period);
    return this.http.get<any>(`${this.apiUrl}/analytics/efficiency/leaderboard`, { params });
  }

  getCampusOverview(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/energy/campus/overview`);
  }

  getCampusStats(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/analytics/campus/stats`);
  }

  compareBuildingEnergy(buildingId: number, compareDays: number = 7): Observable<any> {
    const params = new HttpParams().set('compare_days', compareDays.toString());
    return this.http.get<any>(`${this.apiUrl}/energy/buildings/${buildingId}/comparison`, { params });
  }

  // ML Analytics endpoints
  detectAnomalies(buildingId: number, hoursBack: number = 24): Observable<any> {
    const params = new HttpParams().set('hours_back', hoursBack.toString());
    return this.http.get<any>(`${this.apiUrl}/ml/anomaly-detection/${buildingId}`, { params });
  }

  getAIInsights(buildingId: number, daysBack: number = 7): Observable<any> {
    const params = new HttpParams().set('days_back', daysBack.toString());
    return this.http.get<any>(`${this.apiUrl}/ml/insights/${buildingId}`, { params });
  }

  getEnergyForecastML(buildingId: number, hoursAhead: number = 24): Observable<any> {
    const params = new HttpParams().set('hours_ahead', hoursAhead.toString());
    return this.http.get<any>(`${this.apiUrl}/ml/forecast/${buildingId}`, { params });
  }

  getEfficiencyLeaderboardML(limit: number = 10): Observable<any> {
    const params = new HttpParams().set('limit', limit.toString());
    return this.http.get<any>(`${this.apiUrl}/ml/leaderboard`, { params });
  }

  trainAnomalyModel(buildingId: number, daysBack: number = 30): Observable<any> {
    const params = new HttpParams().set('days_back', daysBack.toString());
    return this.http.post<any>(`${this.apiUrl}/ml/anomaly-detection/train/${buildingId}`, {}, { params });
  }

  // WebSocket Methods
  private initWebSocket() {
    if (!this.websocket || this.websocket.readyState === WebSocket.CLOSED) {
      try {
        this.websocket = new WebSocket(this.wsUrl);
        
        this.websocket.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.wsConnectionSubject.next(true);
          
          // Subscribe to selected building updates
          this.selectedBuilding$.subscribe(buildingId => {
            if (buildingId && this.websocket?.readyState === WebSocket.OPEN) {
              this.websocket.send(JSON.stringify({
                type: 'subscribe_building',
                building_id: buildingId
              }));
            }
          });
        };

        this.websocket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.websocket.onclose = () => {
          console.log('WebSocket disconnected');
          this.wsConnectionSubject.next(false);
          this.attemptReconnect();
        };

        this.websocket.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.wsConnectionSubject.next(false);
        };
      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
      }
    }
  }

  private handleWebSocketMessage(data: any) {
    switch (data.type) {
      case 'energy_update':
        const currentData = this.realTimeDataSubject.value;
        const newReading: EnergyReading = {
          timestamp: data.timestamp,
          meter_reading: data.meter_reading,
          meter_type: data.meter_type,
          air_temperature: data.air_temperature
        };
        const updatedData = [...currentData.slice(-23), newReading];
        this.realTimeDataSubject.next(updatedData);
        break;
      
      case 'anomaly_alert':
        console.log('Anomaly detected:', data);
        // Handle anomaly alerts
        break;
      
      case 'system_status':
        console.log('System status update:', data);
        break;
      
      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.initWebSocket();
      }, 2000 * this.reconnectAttempts); // Exponential backoff
    } else {
      console.error('Max WebSocket reconnect attempts exceeded');
    }
  }

  public disconnectWebSocket() {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = undefined;
    }
  }
}