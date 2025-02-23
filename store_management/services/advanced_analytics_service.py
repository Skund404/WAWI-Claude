# Path: services/advanced_analytics_service.py
"""
Advanced Analytics Service for Leatherworking Project Management

Provides comprehensive analytics and insights across material, project,
and inventory management.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import statistics
import json
import matplotlib.pyplot as plt

# Import other services for comprehensive analysis
from services.material_management_service import MaterialManagementService
from services.project_workflow_manager import ProjectWorkflowManager


class AdvancedAnalyticsService:
    """
    Comprehensive analytics service for leatherworking project management.

    Provides insights across:
    - Material efficiency
    - Project performance
    - Inventory optimization
    - Cost analysis
    """

    def __init__(self, material_service: MaterialManagementService, project_service: ProjectWorkflowManager):
        """
        Initialize the Advanced Analytics Service.

        Args:
            material_service (MaterialManagementService): Material management service
            project_service (ProjectWorkflowManager): Project workflow manager
        """
        self.material_service = material_service
        self.project_service = project_service
        self.logger = logging.getLogger(__name__)

    def generate_material_efficiency_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive material efficiency report.

        Returns:
            Dict: Detailed material efficiency analysis
        """
        efficiency_report = self.material_service.get_material_efficiency_report()

        # Advanced analysis
        analysis = {
            'overall_efficiency': {},
            'material_details': {}
        }

        # Calculate overall efficiency metrics
        efficiency_rates = []
        for material_id, material_data in efficiency_report.items():
            if isinstance(material_data, dict):
                efficiency_rates.append(material_data.get('efficiency_rate', 0))

                # Detailed material analysis
                analysis['material_details'][material_id] = {
                    'total_used': material_data.get('total_used', 0),
                    'total_wasted': material_data.get('total_wasted', 0),
                    'efficiency_rate': material_data.get('efficiency_rate', 0),
                    'projects_used': material_data.get('projects', [])
                }

        # Calculate overall efficiency statistics
        if efficiency_rates:
            analysis['overall_efficiency'] = {
                'mean_efficiency': statistics.mean(efficiency_rates),
                'median_efficiency': statistics.median(efficiency_rates),
                'min_efficiency': min(efficiency_rates),
                'max_efficiency': max(efficiency_rates)
            }

        return analysis

    def project_performance_analysis(self) -> Dict[str, Any]:
        """
        Analyze project performance across multiple dimensions.

        Returns:
            Dict: Comprehensive project performance analysis
        """
        # Get all projects
        projects = self.project_service.get_all_projects()

        # Performance analysis structure
        performance_analysis = {
            'overall_metrics': {
                'total_projects': 0,
                'average_progress': 0.0,
                'project_status_distribution': {}
            },
            'project_details': []
        }

        # Collect project data
        progress_values = []
        status_distribution = {}

        for project in projects:
            # Count total projects
            performance_analysis['overall_metrics']['total_projects'] += 1

            # Track progress
            progress = project.get('progress', 0)
            progress_values.append(progress)

            # Track status distribution
            status = project.get('status', 'UNKNOWN')
            status_distribution[status] = status_distribution.get(status, 0) + 1

            # Collect detailed project information
            performance_analysis['project_details'].append({
                'id': project.get('id'),
                'name': project.get('name'),
                'type': project.get('type'),
                'skill_level': project.get('skill_level'),
                'status': status,
                'progress': progress,
                'materials': project.get('materials', {}),
                'tasks': project.get('tasks', [])
            })

        # Calculate overall metrics
        if progress_values:
            performance_analysis['overall_metrics'].update({
                'average_progress': statistics.mean(progress_values),
                'project_status_distribution': status_distribution
            })

        return performance_analysis

    def material_cost_analysis(self) -> Dict[str, Any]:
        """
        Perform comprehensive material cost analysis.

        Returns:
            Dict: Detailed material cost breakdown and insights
        """
        # Get material allocation status
        material_allocations = self.material_service.get_material_allocation_status()

        # Cost analysis structure
        cost_analysis = {
            'total_materials': 0,
            'total_allocated_quantity': 0.0,
            'material_cost_breakdown': {},
            'allocation_efficiency': {}
        }

        for material_id, allocation_data in material_allocations.items():
            # Skip if not a valid allocation
            if not isinstance(allocation_data, dict):
                continue

            cost_analysis['total_materials'] += 1
            total_quantity = allocation_data.get('total_quantity', 0)
            allocated_quantity = allocation_data.get('allocated_quantity', 0)

            # Accumulate total allocated quantity
            cost_analysis['total_allocated_quantity'] += allocated_quantity

            # Material cost details
            cost_analysis['material_cost_breakdown'][material_id] = {
                'total_quantity': total_quantity,
                'allocated_quantity': allocated_quantity,
                'allocation_percentage': (allocated_quantity / total_quantity * 100) if total_quantity > 0 else 0,
                'status': allocation_data.get('status', 'UNKNOWN')
            }

            # Allocation efficiency calculation
            cost_analysis['allocation_efficiency'][material_id] = {
                'allocation_rate': (allocated_quantity / total_quantity * 100) if total_quantity > 0 else 0,
                'remaining_quantity': total_quantity - allocated_quantity
            }

        return cost_analysis

    def generate_visualization(self, analysis_type: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Generate visualizations for different types of analyses.

        Args:
            analysis_type (str): Type of analysis to visualize
            output_path (Optional[str]): Path to save visualization

        Returns:
            Optional[str]: Path to saved visualization
        """
        plt.figure(figsize=(10, 6))

        if analysis_type == 'material_efficiency':
            # Material Efficiency Visualization
            efficiency_report = self.generate_material_efficiency_report()

            # Extract efficiency rates
            materials = list(efficiency_report['material_details'].keys())
            efficiency_rates = [
                details['efficiency_rate']
                for details in efficiency_report['material_details'].values()
            ]

            plt.bar(materials, efficiency_rates)
            plt.title('Material Efficiency Rates')
            plt.xlabel('Material ID')
            plt.ylabel('Efficiency Rate (%)')
            plt.xticks(rotation=45)
            plt.tight_layout()

        elif analysis_type == 'project_performance':
            # Project Performance Visualization
            performance_analysis = self.project_performance_analysis()

            # Extract project progress data
            projects = [detail['name'] for detail in performance_analysis['project_details']]
            progress_values = [detail['progress'] for detail in performance_analysis['project_details']]

            plt.bar(projects, progress_values)
            plt.title('Project Progress')
            plt.xlabel('Project Name')
            plt.ylabel('Progress (%)')
            plt.xticks(rotation=45)
            plt.tight_layout()

        elif analysis_type == 'material_allocation':
            # Material Allocation Visualization
            cost_analysis = self.material_cost_analysis()

            # Prepare data for visualization
            materials = list(cost_analysis['material_cost_breakdown'].keys())
            allocation_percentages = [
                details['allocation_percentage']
                for details in cost_analysis['material_cost_breakdown'].values()
            ]

            plt.bar(materials, allocation_percentages)
            plt.title('Material Allocation Percentage')
            plt.xlabel('Material ID')
            plt.ylabel('Allocation Percentage (%)')
            plt.xticks(rotation=45)
            plt.tight_layout()

        else:
            self.logger.warning(f"Unsupported visualization type: {analysis_type}")
            plt.close()
            return None

        # Save or display visualization
        if output_path:
            plt.savefig(output_path)
            plt.close()
            return output_path

        plt.show()
        return None

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report combining all analyses.

        Returns:
            Dict: Comprehensive analytics report
        """
        return {
            'material_efficiency': self.generate_material_efficiency_report(),
            'project_performance': self.project_performance_analysis(),
            'material_cost_analysis': self.material_cost_analysis(),
            'report_generated_at': datetime.now()
        }


def main():
    """
    Demonstration of Advanced Analytics Service functionality.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create services
    material_service = MaterialManagementService()
    project_service = ProjectWorkflowManager(material_service)

    # Initialize analytics service
    analytics_service = AdvancedAnalyticsService(material_service, project_service)

    # Register some sample materials
    material_service.register_material('LEATHER-BROWN', 50.0, 'full_grain')
    material_service.register_material('THREAD-STRONG', 200.0, 'polyester')

    # Create a sample project
    project_id = project_service.create_project(
        name="Leather Messenger Bag",
        project_type="Bag",
        skill_level="Advanced"
    )

    # Add materials and update usage
    project_service.add_project_material(project_id, 'LEATHER-BROWN', 10.5, 15.0)
    project_service.update_material_usage(project_id, 'LEATHER-BROWN', 9.8, 0.7)

    # Generate and print comprehensive report
    comprehensive_report = analytics_service.generate_comprehensive_report()
    print("Comprehensive Analytics Report:")
    print(json.dumps(comprehensive_report, indent=2))

    # Generate visualizations
    analytics_service.generate_visualization('material_efficiency', 'material_efficiency.png')
    analytics_service.generate_visualization('project_performance', 'project_performance.png')
    analytics_service.generate_visualization('material_allocation', 'material_allocation.png')


if __name__ == "__main__":
    main()
