"""
Chart Generator for IQStocker Admin Panel
Creates interactive charts using Plotly for dashboard visualization
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class ChartGenerator:
    """Generates interactive charts for admin dashboard"""
    
    def __init__(self):
        # IQStocker brand colors
        self.colors = {
            'primary': '#2563eb',
            'secondary': '#7c3aed',
            'success': '#10b981',
            'danger': '#ef4444',
            'warning': '#f59e0b',
            'info': '#06b6d4',
            'light': '#f8fafc',
            'dark': '#1e293b'
        }
        
        # Chart color palette
        self.palette = [
            self.colors['primary'],
            self.colors['secondary'],
            self.colors['success'],
            self.colors['warning'],
            self.colors['info'],
            self.colors['danger']
        ]
    
    def create_user_growth_chart(self, data: Dict[str, Any]) -> str:
        """Create line chart showing user growth over time"""
        growth_data = data.get('growth_data', [])
        
        if not growth_data:
            return self._create_empty_chart("No growth data available")
        
        months = [item['month'] for item in growth_data]
        users = [item['users'] for item in growth_data]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=months,
            y=users,
            mode='lines+markers',
            name='New Users',
            line=dict(color=self.colors['primary'], width=3),
            marker=dict(size=8, color=self.colors['primary']),
            hovertemplate='<b>%{x}</b><br>New Users: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title={
                'text': 'User Growth Over Time',
                'x': 0.5,
                'font': {'size': 18, 'color': self.colors['dark']}
            },
            xaxis_title='Month',
            yaxis_title='New Users',
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial", size=12),
            margin=dict(l=40, r=40, t=60, b=40),
            hovermode='x unified'
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def create_subscription_pie_chart(self, data: Dict[str, Any]) -> str:
        """Create pie chart showing subscription distribution"""
        subscription_dist = data.get('subscription_distribution', {})
        
        if not subscription_dist:
            return self._create_empty_chart("No subscription data available")
        
        labels = list(subscription_dist.keys())
        values = list(subscription_dist.values())
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker_colors=self.palette[:len(labels)],
            textinfo='label+percent',
            textposition='outside',
            hovertemplate='<b>%{label}</b><br>Users: %{value}<br>Percentage: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title={
                'text': 'Subscription Distribution',
                'x': 0.5,
                'font': {'size': 18, 'color': self.colors['dark']}
            },
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial", size=12),
            margin=dict(l=40, r=40, t=60, b=40),
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.01
            )
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def create_revenue_bar_chart(self, data: Dict[str, Any]) -> str:
        """Create bar chart showing revenue trends"""
        revenue_trends = data.get('revenue_trends', [])
        
        if not revenue_trends:
            return self._create_empty_chart("No revenue data available")
        
        months = [item['month'] for item in revenue_trends]
        revenues = [item['revenue'] for item in revenue_trends]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=months,
            y=revenues,
            name='Monthly Revenue',
            marker_color=self.colors['success'],
            hovertemplate='<b>%{x}</b><br>Revenue: $%{y:,.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            title={
                'text': 'Monthly Revenue Trends',
                'x': 0.5,
                'font': {'size': 18, 'color': self.colors['dark']}
            },
            xaxis_title='Month',
            yaxis_title='Revenue ($)',
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial", size=12),
            margin=dict(l=40, r=40, t=60, b=40),
            hovermode='x unified'
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def create_activity_heatmap(self, data: Dict[str, Any]) -> str:
        """Create heatmap showing user activity patterns"""
        # This would require more detailed activity data
        # For now, create a sample heatmap
        
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        hours = [f'{i:02d}:00' for i in range(24)]
        
        # Sample activity data (would be real data in production)
        activity_data = []
        for day in days:
            day_data = []
            for hour in hours:
                # Simulate activity pattern (more active during business hours)
                hour_num = int(hour.split(':')[0])
                if 9 <= hour_num <= 17:  # Business hours
                    activity = 0.7 + (0.3 * (hour_num % 3) / 3)
                else:
                    activity = 0.2 + (0.3 * (hour_num % 5) / 5)
                day_data.append(activity)
            activity_data.append(day_data)
        
        fig = go.Figure(data=go.Heatmap(
            z=activity_data,
            x=hours,
            y=days,
            colorscale='Blues',
            hovertemplate='<b>%{y} %{x}</b><br>Activity: %{z:.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            title={
                'text': 'User Activity Heatmap',
                'x': 0.5,
                'font': {'size': 18, 'color': self.colors['dark']}
            },
            xaxis_title='Hour of Day',
            yaxis_title='Day of Week',
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial", size=12),
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def create_feature_usage_chart(self, data: Dict[str, Any]) -> str:
        """Create horizontal bar chart showing feature usage"""
        feature_adoption = data.get('feature_adoption', {})
        
        if not feature_adoption:
            return self._create_empty_chart("No feature usage data available")
        
        features = list(feature_adoption.keys())
        adoption_rates = list(feature_adoption.values())
        
        # Format feature names for display
        feature_labels = []
        for feature in features:
            if feature == 'csv_analyses':
                feature_labels.append('CSV Analytics')
            elif feature == 'theme_requests':
                feature_labels.append('Theme Requests')
            else:
                feature_labels.append(feature.replace('_', ' ').title())
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=feature_labels,
            x=adoption_rates,
            orientation='h',
            marker_color=self.colors['info'],
            hovertemplate='<b>%{y}</b><br>Adoption Rate: %{x:.1f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title={
                'text': 'Feature Adoption Rates',
                'x': 0.5,
                'font': {'size': 18, 'color': self.colors['dark']}
            },
            xaxis_title='Adoption Rate (%)',
            yaxis_title='Feature',
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial", size=12),
            margin=dict(l=40, r=40, t=60, b=40),
            xaxis=dict(range=[0, 100])
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def create_popular_themes_chart(self, data: List[Dict[str, Any]]) -> str:
        """Create bar chart showing popular themes"""
        if not data:
            return self._create_empty_chart("No theme data available")
        
        themes = [item['theme'] for item in data[:10]]  # Top 10
        requests = [item['requests'] for item in data[:10]]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=requests,
            y=themes,
            orientation='h',
            marker_color=self.colors['secondary'],
            hovertemplate='<b>%{y}</b><br>Requests: %{x}<extra></extra>'
        ))
        
        fig.update_layout(
            title={
                'text': 'Most Popular Themes',
                'x': 0.5,
                'font': {'size': 18, 'color': self.colors['dark']}
            },
            xaxis_title='Number of Requests',
            yaxis_title='Theme',
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial", size=12),
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def create_conversion_funnel_chart(self, data: Dict[str, Any]) -> str:
        """Create funnel chart showing conversion rates"""
        # Sample conversion data (would be real data in production)
        stages = ['Visitors', 'Registered', 'Trial Users', 'Paid Users']
        values = [1000, 800, 200, 150]  # Sample values
        
        fig = go.Figure(go.Funnel(
            y=stages,
            x=values,
            textinfo="value+percent initial",
            marker=dict(color=self.palette[:len(stages)]),
            hovertemplate='<b>%{y}</b><br>Users: %{x}<extra></extra>'
        ))
        
        fig.update_layout(
            title={
                'text': 'User Conversion Funnel',
                'x': 0.5,
                'font': {'size': 18, 'color': self.colors['dark']}
            },
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial", size=12),
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def create_metrics_gauge(self, value: float, max_value: float, title: str, color: str = 'primary') -> str:
        """Create gauge chart for single metrics"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title},
            delta={'reference': max_value * 0.8},
            gauge={
                'axis': {'range': [None, max_value]},
                'bar': {'color': self.colors.get(color, self.colors['primary'])},
                'steps': [
                    {'range': [0, max_value * 0.5], 'color': "lightgray"},
                    {'range': [max_value * 0.5, max_value * 0.8], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_value * 0.9
                }
            }
        ))
        
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial", size=12),
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def _create_empty_chart(self, message: str) -> str:
        """Create empty chart with message"""
        fig = go.Figure()
        
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color=self.colors['dark'])
        )
        
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    def generate_dashboard_charts(self, metrics_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate all charts for dashboard"""
        charts = {}
        
        try:
            # User metrics charts
            if 'users' in metrics_data:
                charts['user_growth'] = self.create_user_growth_chart(metrics_data['users'])
                charts['subscription_distribution'] = self.create_subscription_pie_chart(metrics_data['users'])
            
            # Financial metrics charts
            if 'financial' in metrics_data:
                charts['revenue_trends'] = self.create_revenue_bar_chart(metrics_data['financial'])
                charts['conversion_funnel'] = self.create_conversion_funnel_chart(metrics_data['financial'])
            
            # Usage metrics charts
            if 'usage' in metrics_data:
                charts['feature_usage'] = self.create_feature_usage_chart(metrics_data['usage'])
                charts['popular_themes'] = self.create_popular_themes_chart(metrics_data['usage'].get('popular_themes', []))
            
            # Activity heatmap
            charts['activity_heatmap'] = self.create_activity_heatmap(metrics_data.get('users', {}))
            
        except Exception as e:
            print(f"Error generating charts: {e}")
            # Return empty charts on error
            charts = {
                'user_growth': self._create_empty_chart("Error loading chart"),
                'subscription_distribution': self._create_empty_chart("Error loading chart"),
                'revenue_trends': self._create_empty_chart("Error loading chart"),
                'feature_usage': self._create_empty_chart("Error loading chart"),
                'popular_themes': self._create_empty_chart("Error loading chart"),
                'activity_heatmap': self._create_empty_chart("Error loading chart")
            }
        
        return charts
