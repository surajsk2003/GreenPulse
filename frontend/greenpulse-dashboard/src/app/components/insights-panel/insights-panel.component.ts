import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Insight } from '../../services/energy.service';

@Component({
  selector: 'app-insights-panel',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './insights-panel.component.html',
  styleUrls: ['./insights-panel.component.scss']
})
export class InsightsPanelComponent {
  @Input() insights: Insight[] = [];
  @Input() loading: boolean = false;
  @Output() insightImplemented = new EventEmitter<Insight>();
  @Output() insightDismissed = new EventEmitter<Insight>();

  trackByInsightId(index: number, insight: Insight): string {
    return insight.id;
  }

  getPriorityLevel(priority: number): string {
    if (priority >= 0.8) return 'high';
    if (priority >= 0.6) return 'medium';
    return 'low';
  }

  getInsightIcon(type: string): string {
    const icons: { [key: string]: string } = {
      'peak_usage': '⚡',
      'weekend_waste': '📅',
      'hvac_efficiency': '🌡️',
      'equipment_schedule': '⚙️',
      'lighting_optimization': '💡'
    };
    return icons[type] || '📊';
  }

  getInsightTypeLabel(type: string): string {
    const labels: { [key: string]: string } = {
      'peak_usage': 'Peak Usage',
      'weekend_waste': 'Weekend Waste',
      'hvac_efficiency': 'HVAC Efficiency',
      'equipment_schedule': 'Equipment Schedule',
      'lighting_optimization': 'Lighting'
    };
    return labels[type] || type.replace('_', ' ');
  }

  implementInsight(insight: Insight) {
    this.insightImplemented.emit(insight);
  }

  dismissInsight(insight: Insight) {
    this.insightDismissed.emit(insight);
  }
}