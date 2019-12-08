from airport.forms import AirportForm
from django.contrib.gis import admin
from django.utils.html import format_html
from airport.models import SurfaceType, Airport, SurfaceShape, AssetType, \
    Asset, AssetCategory, AssetVersion, Translation


class AirportAdmin(admin.ModelAdmin):
    form = AirportForm


class AssetTypeAdmin(admin.ModelAdmin):

    def image_tag(self, obj):
        return format_html('<img src="{}" />'.format(obj.icon.url))

    image_tag.short_description = 'Image'
    list_display = ['name', 'category', 'image_tag', ]


admin.site.register(AssetType, AssetTypeAdmin)
admin.site.register(Airport, AirportAdmin)
admin.site.register(SurfaceType)
admin.site.register(AssetCategory)
admin.site.register(SurfaceShape, admin.GeoModelAdmin)
admin.site.register(Asset, admin.OSMGeoAdmin)
admin.site.register(AssetVersion)
admin.site.register(Translation)
