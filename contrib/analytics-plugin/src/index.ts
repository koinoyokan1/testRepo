import axios from 'axios';
import * as _ from 'lodash';

interface AnalyticsEvent {
  userId: string;
  eventType: string;
  timestamp: number;
  metadata?: Record<string, any>;
}

export class AnalyticsTracker {
  private events: AnalyticsEvent[] = [];

  async track(event: AnalyticsEvent): Promise<void> {
    this.events.push(event);
    
    // Send to analytics backend
    try {
      await axios.post('http://localhost:9000/analytics', event);
    } catch (error) {
      console.error('Failed to send analytics event:', error);
    }
  }

  getEventsByUser(userId: string): AnalyticsEvent[] {
    return _.filter(this.events, { userId });
  }
}
