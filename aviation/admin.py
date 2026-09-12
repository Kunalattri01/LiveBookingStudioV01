# from django.contrib import admin
# from aviation.models import AircraftCategory, Aircraft, AircraftImage, AircraftSpecification, AircraftFeature, AircraftService



# @admin.register(AircraftCategory)
# class AircraftCategoryAdmin(admin.ModelAdmin):

#     list_display = ("name", "is_active", "display_order", "created_at")
#     list_filter = ("is_active",)
#     search_fields = ("name", "slug")
#     prepopulated_fields = {
#         "slug": ("name",)
#     }


# @admin.register(Aircraft)
# class AircraftAdmin(admin.ModelAdmin):

#     list_display = ("name", "category", "aircraft_type", "passenger_capacity", "is_featured", "is_active", "display_order")
#     list_filter = (
#         "category",
#         "aircraft_type",
#         "is_featured",
#         "is_active",
#     )
#     search_fields = (
#         "name",
#         "slug",
#         "manufacturer",
#         "model_name",
#     )
#     prepopulated_fields = {
#         "slug": ("name",)
#     }


# @admin.register(AircraftImage)
# class AircraftImageAdmin(admin.ModelAdmin):
#     list_display = (
#         "aircraft",
#         "image_type",
#         "is_primary",
#         "is_active",
#         "display_order",
#     )
#     list_filter = (
#         "image_type",
#         "is_primary",
#         "is_active",
#     )
#     search_fields = (
#         "aircraft__name",
#         "title",
#         "alt_text",
#     )


# @admin.register(AircraftSpecification)
# class AircraftSpecificationAdmin(admin.ModelAdmin):
#     list_display = (
#         "aircraft",
#         "section_name",
#         "label",
#         "value",
#         "unit",
#         "display_order",
#     )
#     list_filter = (
#         "section_name",
#         "is_active",
#     )
#     search_fields = (
#         "aircraft__name",
#         "label",
#         "value",
#     )


# @admin.register(AircraftFeature)
# class AircraftFeatureAdmin(admin.ModelAdmin):
#     list_display = (
#         "aircraft",
#         "title",
#         "is_active",
#         "display_order",
#     )
#     list_filter = ("is_active",)
#     search_fields = (
#         "aircraft__name",
#         "title",
#         "description",
#     )


# @admin.register(AircraftService)
# class AircraftServiceAdmin(admin.ModelAdmin):
#     list_display = (
#         "aircraft",
#         "name",
#         "price",
#         "currency",
#         "is_price_on_request",
#         "is_active",
#         "display_order",
#     )
#     list_filter = (
#         "is_active",
#         "is_price_on_request",
#     )
#     search_fields = (
#         "aircraft__name",
#         "name",
#     )