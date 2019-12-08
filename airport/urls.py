from rest_framework import routers

from airport.views import SurfaceTypeViewSet, AirportViewSet, \
  SurfaceShapeViewSet, AssetTypeViewSet, AssetViewSet, MobileAssetTypeViewSet, \
  MobileSurfaceTypeViewSet, MobileAirportAssetViewSet, MobileSurfaceShapeViewSet, \
  AssetConfigurationViewSet

router = routers.SimpleRouter()
router.register(r'surface_types', SurfaceTypeViewSet,
                base_name='surface_types')
router.register(r'airports', AirportViewSet, base_name='airports')
router.register(r'surface_shapes', SurfaceShapeViewSet,
                base_name='surface_shapes')
router.register(r'asset_types', AssetTypeViewSet,
                base_name='asset_types')
router.register(r'assets', AssetViewSet, base_name='assets')
router.register(r'mobile/asset_types', MobileAssetTypeViewSet,
                base_name='mobile_asset_types')
router.register(r'mobile/surface_types', MobileSurfaceTypeViewSet,
                base_name='mobile_surface_types')
router.register(r'mobile/airport_assets', MobileAirportAssetViewSet, base_name='airport_assets')
router.register(r'mobile/surface_shapes', MobileSurfaceShapeViewSet,
                base_name='mobile_surface_shapes')
router.register(r'asset_configuration', AssetConfigurationViewSet, base_name='asset_configuration')

router.register(r'mobile/asset_configuration', AssetConfigurationViewSet, base_name='mobile_asset_configuration')
router.register(r'mobile/airports', AirportViewSet, base_name='mobile_airports')
urlpatterns = [
]
