from rest_framework import serializers


class AnnotationRequestSerializer(serializers.Serializer):
    variants = serializers.ListField(
        child=serializers.CharField(allow_blank=False, max_length=500),
        allow_empty=False,
        help_text="Variant strings, e.g. '17:43092951 G>A'",
    )
    assembly = serializers.ChoiceField(
        choices=["GRCh37", "GRCh38"],
        default="GRCh37",
    )
    engine = serializers.ChoiceField(
        choices=["vep", "annovar", "both"],
        default="vep",
    )


class VariantResultSerializer(serializers.Serializer):
    input = serializers.CharField()
    allele = serializers.CharField(allow_null=True, required=False)
    gene = serializers.CharField(allow_null=True, required=False)
    feature = serializers.CharField(allow_null=True, required=False)
    consequence = serializers.CharField(allow_null=True, required=False)
    impact = serializers.CharField(allow_null=True, required=False)
    cdot = serializers.CharField(allow_null=True, required=False)
    protein = serializers.CharField(allow_null=True, required=False)
    biotype = serializers.CharField(allow_null=True, required=False)
    canonical = serializers.CharField(allow_null=True, required=False)
    engine = serializers.CharField(required=False)
    details = serializers.DictField(required=False)


class AnnotationResponseSerializer(serializers.Serializer):
    assembly = serializers.CharField()
    engine = serializers.CharField()
    results = VariantResultSerializer(many=True)
