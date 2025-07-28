import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-leaderboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './leaderboard.component.html',
  styleUrls: ['./leaderboard.component.scss']
})
export class LeaderboardComponent {
  @Input() leaderboard: any[] = [];
  @Input() loading: boolean = false;
  @Output() periodChanged = new EventEmitter<string>();

  selectedPeriod: string = 'week';

  trackByBuildingId(index: number, building: any): number {
    return building.building_id;
  }

  onPeriodChange() {
    this.periodChanged.emit(this.selectedPeriod);
  }

  getRankClass(rank: number): string {
    if (rank === 1) return 'gold';
    if (rank === 2) return 'silver';
    if (rank === 3) return 'bronze';
    return 'regular';
  }

  getRankDisplay(rank: number): string {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return rank.toString();
  }

  getScoreClass(score: number): string {
    if (score >= 90) return 'excellent';
    if (score >= 80) return 'good';
    if (score >= 70) return 'average';
    return 'poor';
  }

  getTrendClass(building: any): string {
    // Mock trend calculation
    const trend = Math.random() > 0.5 ? 'up' : 'down';
    return trend;
  }

  getTrendArrow(building: any): string {
    const trend = this.getTrendClass(building);
    return trend === 'up' ? '↗️' : '↘️';
  }

  getAverageEfficiency(): number {
    if (!this.leaderboard || this.leaderboard.length === 0) return 0;
    const sum = this.leaderboard.reduce((acc, building) => acc + building.efficiency_score, 0);
    return sum / this.leaderboard.length;
  }
}