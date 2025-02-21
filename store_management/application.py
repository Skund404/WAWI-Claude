from store_management.services.storage_service import StorageService
from store_management.services.inventory_service import InventoryService
from store_management.services.order_service import OrderService
from store_management.services.recipe_service import RecipeService
from store_management.database.sqlalchemy.session import init_database
import logging


class Application:
    """Main application class responsible for initialization and service creation"""

    def __init__(self, db_url=None):
        """Initialize application with optional database URL"""
        self.db_url = db_url
        self.logger = logging.getLogger(__name__)
        self.services = {}

    def initialize(self):
        """Initialize the application, database connection and create services"""
        self.logger.info("Initializing application")

        # Initialize database
        init_database()

        # Create services
        self.services["storage"] = StorageService()
        self.services["inventory"] = InventoryService()
        self.services["order"] = OrderService()
        self.services["recipe"] = RecipeService()

        self.logger.info("Application initialized successfully")

    def get_service(self, service_name):
        """Get a service by name"""
        return self.services.get(service_name)

    def cleanup(self):
        """Clean up resources"""
        self.logger.info("Cleaning up application resources")
        # Nothing to clean up with the new approach as session management
        # is handled at the function level