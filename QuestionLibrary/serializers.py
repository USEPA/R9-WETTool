from rest_framework.serializers import ModelSerializer, ReadOnlyField, PrimaryKeyRelatedField
from rest_framework.validators import ValidationError
from .models import *


class LookupGroupSerializer(ModelSerializer):
    class Meta:
        model = LookupGroup
        fields = '__all__'


class LookupSerializer(ModelSerializer):
    class Meta:
        model = Lookup
        fields = '__all__'


class MediaSerializer(ModelSerializer):
    class Meta:
        model = Media
        fields = '__all__'


class EPAResponseSerializer(ModelSerializer):
    class Meta:
        model = EPAResponse
        fields = '__all__'


class FacilityTypeSerializer(ModelSerializer):
    class Meta:
        model = FacilityType
        fields = '__all__'


class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class Survey123FieldTypeSerializer(ModelSerializer):
    class Meta:
        model = Survey123FieldType
        fields = '__all__'


class UnitSerializer(ModelSerializer):
    class Meta:
        model = Unit
        fields = '__all__'


class ESRIFieldTypesSerializer(ModelSerializer):
    class Meta:
        model = ESRIFieldTypes
        fields = '__all__'


class MasterQuestionSerializer(ModelSerializer):
    class Meta:
        model = MasterQuestion
        fields = '__all__'


class SurveySerializer(ModelSerializer):
    class Meta:
        model = Survey
        fields = '__all__'


class QuestionSetSerializer(ModelSerializer):
    class Meta:
        model = QuestionSet
        fields = '__all__'


class QuestionListSerializer(ModelSerializer):
    class Meta:
        model = QuestionList
        fields = '__all__'


class SurveyResponseSerializer(ModelSerializer):
    class Meta:
        model = SurveyResponse
        fields = '__all__'


class RelatedQuestionListSerializer(ModelSerializer):
    class Meta:
        model = RelatedQuestionList
        fields = '__all__'


class DashboardSerializer(ModelSerializer):
    class Meta:
        model = Dashboard
        fields = '__all__'