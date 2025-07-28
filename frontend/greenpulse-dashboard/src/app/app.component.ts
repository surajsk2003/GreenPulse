import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';
import { DashboardComponent } from './components/dashboard/dashboard.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, HttpClientModule, DashboardComponent],
  template: `
    <div class="app-container">
      <app-dashboard></app-dashboard>
    </div>
  `,
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'GreenPulse - Smart Energy Management';
}