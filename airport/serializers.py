
from django.db import transaction
from rest_framework_gis import serializers
from rest_framework.serializers import (SerializerMethodField, ValidationError,
                                        ImageField, Serializer)

from pulpoforms.forms import Form as PulpoForm

from forms.utils import PUBLISHED
from airport.models import SurfaceType, Airport, SurfaceShape, AssetType, \
    Asset, AssetVersion, AssetImage, Translation, AssetForm, AssetCategory


class SurfaceTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = SurfaceType
        fields = '__all__'


class AirportSerializer(serializers.ModelSerializer):

    class Meta:
        model = Airport
        fields = '__all__'


class AirportCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Airport
        fields = '__all__'

    def create(self, validated_data):
        instance = Airport.objects.create(**validated_data)
        return instance    


class AirportDetailSerializer(serializers.ModelSerializer):
    location = SerializerMethodField()

    class Meta:
        model = Airport
        fields = '__all__'
    
    def get_location(self, obj):
        if obj.location:
            return {'coordinates': [{'lon': obj.location.x, 'lat': obj.location.y}]}
        else:
            return None

class AirportWebSerializer(serializers.ModelSerializer):
    location = SerializerMethodField()

    class Meta:
        model = Airport
        fields = '__all__'

    def get_location(self, obj):
        if obj.location:
            return {'coordinates': [obj.location.x, obj.location.y]}
        else:
            return None


class SurfaceShapeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurfaceShape
        fields = '__all__'
        geo_field = 'geometry'


class SurfaceShapeDetailSerializer(serializers.ModelSerializer):
    surface_type = SurfaceTypeSerializer()

    class Meta:
        model = SurfaceShape
        fields = '__all__'
        geo_field = 'geometry'


class AssetTypeSerializer(serializers.ModelSerializer):
    category = SerializerMethodField()

    class Meta:
        model = AssetType
        fields = '__all__'

    def get_category(self, obj):
        return obj.category.name


class AssetImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = AssetImage
        fields = ('id', 'asset', 'image')


class AssetSerializer(serializers.ModelSerializer):
    images = AssetImageSerializer(many=True)
    asset_type = AssetTypeSerializer()

    class Meta:
        model = Asset
        fields = ('id', 'name', 'asset_type', 'geometry', 'area', 'label',
                  'response', 'version_schema', 'airport', 'images')

        geo_field = 'geometry'

    def validate(self, data):
        user = self.context['request'].user
        published_version = AssetVersion.objects.get(
            form__airport__id=user.aerosimple_user.airport_id,
            form__category=data['asset_type'].category,
            status=PUBLISHED)

        form = PulpoForm(published_version.schema)
        answers = data['response']
        result = form.check_answers(answers)

        if result['result'] != 'OK':
            raise ValidationError(result.errors)

        return data


class AssetCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Asset
        fields = ('id', 'name', 'asset_type', 'geometry', 'area', 'label',
                  'response', 'version_schema')

        geo_field = 'geometry'

    def validate(self, data):
        user = self.context['request'].user
        published_version = AssetVersion.objects.get(
            form__airport__id=user.aerosimple_user.airport_id,
            form__category=data['asset_type'].category,
            status=PUBLISHED)

        form = PulpoForm(published_version.schema)
        answers = data['response']
        result = form.check_answers(answers)

        if result['result'] != 'OK':
            raise ValidationError(result.errors)

        return data

    def create(self, validated_data):
        asset = Asset(**validated_data)
        asset.airport = self.context['request'].user.aerosimple_user.airport
        asset.save()
        return asset


class AssetListSerializer(serializers.ModelSerializer):
    asset_type = AssetTypeSerializer()
    images = AssetImageSerializer(many=True)
    geometry = SerializerMethodField()

    class Meta:
        model = Asset
        fields = "__all__"
        geo_field = 'geometry'

    def get_geometry(self, obj):
        if obj.geometry:
            return ({"type":obj.geometry.geom_type,"coordinates":[{"lon":obj.geometry.x,"lat":obj.geometry.y}]})
        else:
            return None


class AssetVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetVersion
        fields = "__all__"


class AssetVersionSaveSerializer(serializers.ModelSerializer):

    class Meta:
        model = AssetVersion
        fields = '__all__'

    def validate_schema(self, value):
        form = PulpoForm(value)
        if not form.is_valid():
            raise ValidationError(form.errors)

        if len(value['pages']) > 1:
            raise ValidationError(
                "An Asset Schema can't have more than one page"
            )

        for p in value['pages']:
            if len(p['sections']) != 1:
                raise ValidationError(
                    "An Asset Schema page must have exactly one section"
                )

        return value


class MobileAssetTypeSerializer(serializers.ModelSerializer):
    image_id = SerializerMethodField()
    

    class Meta:
        model = AssetType
        fields = ('id', 'name', 'category', 'image_id')

    def get_image_id(self, obj):
        id = "asset_type_"+str(obj.id)
        return id


class MobileSurfaceTypeSerializer(serializers.ModelSerializer):
    icon = SerializerMethodField()
    category = SerializerMethodField()

    class Meta:
        model = SurfaceType
        fields = ('category','icon','id', 'color','name')

    def get_icon(self, obj):
        asset = AssetForm.objects.filter(airport__id=obj.airport.id).first()
        asset_type = AssetType.objects.filter(category__id=asset.category.id).first()
        if asset_type:
            return asset_type.icon.url
        return None

    def get_category(self, obj):
        asset = AssetForm.objects.filter(airport__id=obj.airport.id).first()
        return asset.category.name


class MobileAirportAssetSerializer(serializers.ModelSerializer):
    asset_type = MobileAssetTypeSerializer()
    images = AssetImageSerializer(many=True)
    geometry = SerializerMethodField()

    class Meta:
        model = Asset
        fields = "__all__"
        geo_field = 'geometry'

    def get_geometry(self, obj):
        if obj.geometry:
            return ({"type":obj.geometry.geom_type,"coordinates":[{'lat':obj.geometry.x,'lon':obj.geometry.y}]})
        else:
            return None


class MobileAssetConfigurationSerializer(serializers.ModelSerializer):
    category = SerializerMethodField()
    comment = SerializerMethodField()
    subCategory = SerializerMethodField()

    class Meta:
        model = Asset
        fields = ('id', 'comment', 'asset_type', 'category', 'subCategory')

    def get_category(self, obj):
        return obj.asset_type.category.id

    def get_comment(self, obj):
        return obj.name

    def get_subCategory(self, obj):
        return None


class AssetCategorySerializer(serializers.ModelSerializer):
    sub_category = SerializerMethodField()

    class Meta:
        model = AssetCategory
        fields = '__all__'

    def get_sub_category(self, obj):
        return None


class AssetConfigurationSerializer(Serializer):
    category = AssetCategorySerializer(many=True)
    category_assets = MobileAssetConfigurationSerializer(many=True)


# ****************************************************************
# *************** ASSETS SERIALIZERS WEB API *********************
# ****************************************************************

class AssetListWebSerializer(serializers.ModelSerializer):
    asset_type = AssetTypeSerializer()
    images = AssetImageSerializer(many=True)
    geometry = SerializerMethodField()

    class Meta:
        model = Asset
        fields = "__all__"
        geo_field = 'geometry'

    def get_geometry(self, obj):
        if obj.geometry:
            return ({"type":obj.geometry.geom_type,"coordinates":[obj.geometry.x,obj.geometry.y]})
        else:
            return None