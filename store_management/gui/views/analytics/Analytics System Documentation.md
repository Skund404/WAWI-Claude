# Analytics System Documentation

## Overview

The analytics system provides comprehensive business intelligence capabilities for the leatherworking ERP. It enables users to analyze data across multiple dimensions to gain insights into business performance, identify trends, and make data-driven decisions.

### System Architecture

The analytics system follows a layered architecture:

1. **Data Access Layer**: Repository classes for retrieving and querying data
2. **Service Layer**: Analytics services that process and transform data
3. **Presentation Layer**: Analytics views that visualize the data

### Components

- **Data Transfer Objects (DTOs)**: Structured data containers for analytics results
- **Analytics Services**: Business logic for data analysis and metrics calculation
- **Visualization Components**: Charts, graphs, and data display widgets
- **Analytics Views**: User interface components for interactive analytics

## Analytics Modules

### Customer Analytics

The customer analytics module provides insights into customer behavior, segmentation, and lifecycle value.

#### Features:

- **Customer Segmentation**: Groups customers based on recency, frequency, and monetary value (RFM analysis)
- **Retention Analysis**: Cohort-based visualization of customer retention over time
- **Lifetime Value Calculation**: Estimates the total worth of a customer to the business
- **Purchase Patterns**: Analyzes frequency, order value, and product preferences

#### Key Metrics:

- Customer acquisition rate
- Customer retention rate
- Average order value by customer segment
- Customer lifetime value
- Purchase frequency
- Repeat customer rate

#### Visualizations:

- Customer segment distribution (pie chart)
- Retention heatmap by cohort
- Lifetime value by segment (bar chart)
- Purchase frequency trend (line chart)

### Profitability Analytics

The profitability analytics module analyzes revenue, costs, and margins across different dimensions.

#### Features:

- **Margin Analysis**: Breaks down profit margins by product type and project type
- **Cost Structure Analysis**: Visualizes cost components and their impact on profitability
- **Trend Analysis**: Tracks profitability metrics over time
- **Comparative Analysis**: Compares profitability across different categories

#### Key Metrics:

- Gross margin percentage
- Contribution margin
- Project profitability
- Cost breakdown
- Revenue and cost trends
- Profit per hour of labor

#### Visualizations:

- Margin by product/project type (bar chart)
- Cost breakdown (pie chart)
- Margin trend over time (line chart)
- Revenue vs costs (multi-line chart)

### Material Usage Analytics

The material usage analytics module provides insights into material consumption, waste, and inventory efficiency.

#### Features:

- **Material Consumption Analysis**: Tracks usage patterns across material types
- **Waste Analysis**: Identifies areas with high waste percentages
- **Inventory Turnover**: Analyzes efficiency of inventory usage
- **Cost Trends**: Monitors material cost changes over time

#### Key Metrics:

- Material consumption by type
- Waste percentage
- Inventory turnover rate
- Days in inventory
- Material cost trends
- Utilization efficiency

#### Visualizations:

- Material consumption by type (pie chart)
- Waste percentage by material (bar chart)
- Inventory turnover (gauge chart)
- Material cost trends (line chart)

### Project Metrics Analytics

The project metrics analytics module analyzes project efficiency, timelines, and resource utilization.

#### Features:

- **Completion Time Analysis**: Tracks project durations across different project types
- **Phase Analysis**: Identifies bottlenecks in the project workflow
- **Resource Utilization**: Analyzes efficiency of material and tool usage
- **Bottleneck Identification**: Highlights constraints in the production process

#### Key Metrics:

- Average completion time
- On-time completion percentage
- Phase durations
- Resource efficiency
- Bottleneck impact score
- Time allocation across activities

#### Visualizations:

- Completion time by project type (bar chart)
- Phase duration heatmap
- Resource utilization (pie charts)
- Bottleneck analysis (bar chart)

## Using the Analytics System

### Accessing Analytics

Analytics can be accessed in several ways:

1. From the main dashboard via the "View Analytics" button or specific analytics links
2. From the main navigation menu's "Analytics" section
3. From contextual links within other modules (e.g., "Analyze Customers" in the customer module)

### Navigation Between Analytics Views

The analytics system provides seamless navigation between different analytics modules:

- The analytics dashboard provides an overview with links to detailed views
- Each detailed view has links to related analytics modules
- Breadcrumb navigation helps track location within the analytics system

### Common Functionality

#### Date Range Selection

All analytics views provide date filtering capabilities:

- Predefined ranges: Last 30 days, Last 90 days, Last 6 months, Last 12 months, Year to date
- Custom date range selection with calendar pickers
- Period comparison for trend analysis

#### Filtering and Segmentation

Analytics views support various filtering options:

- Material type filtering in material usage analytics
- Project type filtering in project metrics and profitability analytics
- Customer segment filtering in customer analytics
- Category filtering in profitability analytics

#### Export Capabilities

Analytics results can be exported in various formats:

- PDF reports with visualization and data tables
- Excel spreadsheets for further analysis
- Raw data export for advanced users

### Responsive Visualizations

All charts and visualizations are designed to be responsive:

- Tooltips provide detailed information on hover
- Legends can be toggled to show/hide data series
- Many visualizations support zooming and panning
- Charts adapt to different screen sizes

## Technical Reference

### Service Interfaces

The analytics system defines the following service interfaces:

- `ICustomerAnalyticsService`: Customer analysis capabilities
- `IProfitabilityAnalyticsService`: Profitability analysis capabilities
- `IMaterialUsageAnalyticsService`: Material analysis capabilities
- `IProjectMetricsService`: Project analysis capabilities
- `IAnalyticsDashboardService`: Integrated analytics for dashboard display

### Analytics DTOs

Key data transfer objects include:

- `CustomerAnalyticsDTO` & `CustomerSegmentDTO`
- `ProfitabilityAnalyticsDTO` & `ProfitMarginDTO`
- `MaterialUsageAnalyticsDTO` & `MaterialUsageItemDTO`
- `ProjectMetricsDTO` & `ProjectPhaseMetricsDTO`
- `AnalyticsSummaryDTO`

### Visualization Components

The system includes these visualization components:

- Bar chart: For comparing values across categories
- Line chart: For displaying trends over time
- Pie chart: For showing proportion and distribution
- Heatmap chart: For multi-dimensional data visualization
- Gauge chart: For displaying single KPI metrics

## Extension Guidelines

### Adding New Analytics Metrics

To add new analytics metrics:

1. Add the metric to the appropriate analytics DTO
2. Implement calculation logic in the service implementation
3. Update the UI to display the new metric

### Creating New Analytics Views

To create a new analytics view:

1. Create a new view class extending `BaseView`
2. Implement the required sections (filters, visualizations, etc.)
3. Register the view in the analytics module initialization

### Adding New Visualization Types

To add a new visualization type:

1. Create a new chart component in the `gui/widgets/charts` directory
2. Implement the rendering and interaction logic
3. Add helper functions in the `charts/__init__.py` file
4. Use the new chart type in analytics views

### Integrating with Other Modules

To integrate analytics with other modules:

1. Add navigation links in the module's views
2. Pass relevant context data to the analytics view
3. Implement any module-specific analytics services if needed