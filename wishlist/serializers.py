from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .models import Wishlist, WishlistItem


class WishlistItemSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField(write_only=True)
    content_type_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = WishlistItem
        fields = [
            "id", "content_type", "content_type_name", "object_id", "title",
            "subtitle", "image_url", "metadata", "created_at",
        ]
        read_only_fields = ["id", "content_type_name", "created_at"]

    def get_content_type_name(self, obj):
        return f"{obj.content_type.app_label}.{obj.content_type.model}"

    def validate_content_type(self, value):
        try:
            app_label, model = value.lower().split(".", 1)
        except ValueError:
            raise serializers.ValidationError("Use content_type in the form app_label.model.")

        if not ContentType.objects.filter(app_label=app_label, model=model).exists():
            raise serializers.ValidationError("The requested content type does not exist.")
        return value.lower()

    def create(self, validated_data):
        request = self.context["request"]
        content_type_name = validated_data.pop("content_type")
        app_label, model = content_type_name.split(".", 1)
        content_type = ContentType.objects.get(app_label=app_label, model=model)

        wishlist = request.user.wishlists.filter(is_default=True).first()
        if wishlist is None:
            wishlist = Wishlist.objects.create(
                user=request.user,
                name="My Wishlist",
                is_default=True,
            )

        return WishlistItem.objects.create(
            wishlist=wishlist,
            content_type=content_type,
            **validated_data,
        )


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "name", "is_default", "items", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
