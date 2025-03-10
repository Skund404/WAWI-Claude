# Mapping of service names to mock implementations
MOCK_SERVICES = {
    'IPatternService': MockBaseService,
    'IToolListService': MockBaseService,
    'ISupplierService': MockBaseService,
    'ILeatherService': MockBaseService,
    'IHardwareService': MockBaseService,
    'ISuppliesService': MockBaseService,
    'IComponentService': MockBaseService,
    'IProductService': MockBaseService,
    'IPurchaseService': MockBaseService,
    'IPickingListService': MockBaseService,
    'IToolService': MockBaseService,
}


def get_mock_service(service_name):
    """Get a mock service implementation.

    Args:
        service_name: Name of the service interface

    Returns:
        Mock service instance or None if not implemented
    """
    service_class = MOCK_SERVICES.get(service_name)
    if service_class:
        return service_class()
    return None