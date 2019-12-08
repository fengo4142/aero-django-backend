from rest_framework import routers
from inspections.views import InspectionViewSet, InspectionAnswerViewSet,\
  InspectionEditViewSet, RemarkViewSet, InspectionTemplateViewSet, ExportViewSet, ExportDataViewSet,\
  InspectionTypeViewSet, MobileInspectionTypeViewSet, ImagesDataViewSet, MobileInspectionAnswersViewSet,\
    SafetySelfInspectionViewSet, AllImagesViewSet, MobileInspectionsViewSet


router = routers.SimpleRouter()
router.register(r'inspections', InspectionViewSet, base_name='inspections')
router.register(r'remarks', RemarkViewSet, base_name='remarks')
router.register(r'inspection_templates', InspectionTemplateViewSet,
                base_name='inspection_templates')
router.register(r'edit_inspections', InspectionEditViewSet,
                base_name='edit_inspections')
router.register(r'inspection_answers', InspectionAnswerViewSet,
                base_name='inspections_answers')
router.register(r'inspection_template', ExportViewSet, base_name='inspection_template')
router.register(r'inspection_template_data', ExportDataViewSet, base_name='inspection_template_data')
router.register(r'inspection_type', InspectionTypeViewSet, base_name='inspection_type')

router.register(r'mobile/inspection_type', MobileInspectionTypeViewSet, base_name='mobile_inspection_type')
router.register(r'mobile/inspection_answers', MobileInspectionAnswersViewSet, base_name='mobile_inspection_answers')
router.register(r'mobile/remarks', RemarkViewSet, base_name='mobile_remarks')
router.register(r'mobile/edit_inspections', InspectionEditViewSet,
                base_name='mobile_edit_inspections')
router.register(r'mobile/inspection_export', ExportViewSet, base_name='mobile_inspection_template')
router.register(r'mobile/inspection_export_data', ExportDataViewSet, base_name='mobile_inspection_template_data')
router.register(r'mobile/images/icons', ImagesDataViewSet, base_name='images_icons')
router.register(r'mobile/asset_category', SafetySelfInspectionViewSet, base_name='asset_category')
router.register(r'mobile/images',AllImagesViewSet, base_name='images')
router.register(r'mobile/inspections',MobileInspectionsViewSet, base_name='mobile_inspections')

urlpatterns = [
]
