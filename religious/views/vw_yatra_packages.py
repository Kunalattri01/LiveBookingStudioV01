from django.db.models import Prefetch
from django.views.generic import DetailView

from religious.models import (
    YatraPackage,
    PackageImage,
)


class YatraPackageDetailView(DetailView):
    model = YatraPackage
    template_name = "religious/yatra_package_detail.html"
    context_object_name = "package"

    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            YatraPackage.objects
            .filter(is_active=True)
            .select_related(
                "baggage_policy",
                "cancellation_policy",
            )
            .prefetch_related(
                "features",
                "pricing_options",
                "pricing_rules",
                "itinerary_days",
                "inclusions",
                "exclusions",
                "guidelines",
                "safety_guidelines",
                "hotels",
                "booking_steps",
                "cancellation_policy__rules",

                Prefetch(
                    "images",
                    queryset=PackageImage.objects.filter(
                        is_active=True
                    ).order_by("display_order", "id"),
                    to_attr="active_package_images",
                ),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        package = self.object

        # Images are already prefetched and filtered.
        images = package.active_package_images

        context.update({
            "features": package.features.filter(is_active=True),
            "pricing_options": package.pricing_options.filter(is_active=True),
            "pricing_rules": package.pricing_rules.filter(is_active=True),
            "itinerary_days": package.itinerary_days.all(),
            "inclusions": package.inclusions.filter(is_active=True),
            "exclusions": package.exclusions.filter(is_active=True),
            "guidelines": package.guidelines.filter(is_active=True),

            "baggage_policy": getattr(
                package,
                "baggage_policy",
                None,
            ),

            "cancellation_policy": getattr(
                package,
                "cancellation_policy",
                None,
            ),

            "safety_guidelines": package.safety_guidelines.filter(
                is_active=True
            ),

            "hotels": package.hotels.filter(is_active=True),
            "booking_steps": package.booking_steps.filter(is_active=True),

            # =====================================================
            # IMAGES
            # =====================================================

            "package_images": images,

            "hero_image": next(
                (
                    image
                    for image in images
                    if image.image_type == PackageImage.ImageType.HERO
                ),
                None,
            ),

            "experience_images": [
                image
                for image in images
                if image.image_type == PackageImage.ImageType.EXPERIENCE
            ],

            "destination_images": [
                image
                for image in images
                if image.image_type == PackageImage.ImageType.DESTINATION
            ],

            "itinerary_images": [
                image
                for image in images
                if image.image_type == PackageImage.ImageType.ITINERARY
            ],

            "hotel_images": [
                image
                for image in images
                if image.image_type == PackageImage.ImageType.HOTEL
            ],

            "gallery_images": [
                image
                for image in images
                if image.image_type == PackageImage.ImageType.GALLERY
            ],

            "contact": None,
        })

        return context